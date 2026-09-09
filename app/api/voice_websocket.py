import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from threading import Event

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.agent_trace import AgentTrace
from app.services.groq_stt import GroqSTTService
from app.services.groq_streaming import GroqStreamingService
from app.services.groq_tts import GroqTTSService


router = APIRouter()


stt_service = GroqSTTService()
streaming_service = GroqStreamingService()
tts_service = GroqTTSService()


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
):
    """
    Real-time voice WebSocket.

    Handles:

        Browser
            ↓
        Audio chunks
            ↓
        Final recording
            ↓
        STT
            ↓
        Streaming LLM
            ↓
        Response chunking
            ↓
        TTS
            ↓
        Audio response

    Also supports:

        - Barge-in
        - LLM interruption
        - TTS cancellation
        - Agent tracing
    """

    await websocket.accept()

    print(
        "[WebSocket] Voice session connected."
    )

    await websocket.send_json(
        {
            "type": "session_started",
            "message": (
                "Live voice session connected."
            ),
        }
    )

    # ---------------------------------------------------------
    # Session state
    # ---------------------------------------------------------

    audio_chunks = []

    total_audio_bytes = 0

    chunk_number = 0

    expecting_final_audio = False

    final_audio_mime_type = (
        "audio/webm"
    )

    interrupt_event = Event()

    # Used to identify whether an AI response
    # is currently being generated.
    ai_response_active = False

    # ---------------------------------------------------------
    # Process one complete voice turn
    # ---------------------------------------------------------

    async def process_voice_turn(
        websocket: WebSocket,
        audio_data: bytes,
        mime_type: str,
        interrupt_event: Event,
    ):

        nonlocal ai_response_active

        trace = AgentTrace()

        trace.record(
            "voice",
            "started",
            audio_size_bytes=len(audio_data),
            mime_type=mime_type,
        )

        temp_path = None

        try:

            # =================================================
            # STT
            # =================================================

            await websocket.send_json(
                {
                    "type": "stt_started"
                }
            )

            with trace.stage("stt"):

                suffix = ".webm"

                if "wav" in mime_type:
                    suffix = ".wav"

                elif "ogg" in mime_type:
                    suffix = ".ogg"

                elif "mp4" in mime_type:
                    suffix = ".mp4"

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                ) as temp_file:

                    temp_file.write(
                        audio_data
                    )

                    temp_path = (
                        temp_file.name
                    )

                stt_result = (
                    stt_service.transcribe(
                        temp_path
                    )
                )

            transcript = stt_result[
                "text"
            ]

            trace.record(
                "stt",
                "result",
                transcript=transcript,
                latency_ms=stt_result[
                    "latency_ms"
                ],
                model=stt_result[
                    "model"
                ],
            )

            await websocket.send_json(
                {
                    "type": "transcript",
                    "text": transcript,
                    "stt_latency_ms": (
                        stt_result[
                            "latency_ms"
                        ]
                    ),
                    "model": stt_result[
                        "model"
                    ],
                }
            )

            # =================================================
            # LLM
            # =================================================

            if not transcript.strip():

                trace.record(
                    "llm",
                    "skipped",
                    reason="empty_transcript",
                )

                await websocket.send_json(
                    {
                        "type": "agent_trace",
                        **trace.get_trace(),
                    }
                )

                return

            await websocket.send_json(
                {
                    "type": (
                        "ai_response_started"
                    )
                }
            )

            ai_response_active = True

            chunk_events = []

            def on_chunk(
                text_chunk: str,
            ):

                chunk_events.append(
                    {
                        "chunk_number": len(
                            chunk_events
                        )
                        + 1,
                        "text": text_chunk,
                        "timestamp_ms": round(
                            (
                                time.perf_counter()
                                - trace.pipeline_start
                            )
                            * 1000,
                            2,
                        ),
                    }
                )

            with trace.stage("llm"):

                llm_result = (
                    await asyncio.to_thread(
                        streaming_service.stream_response,
                        transcript,
                        None,
                        on_chunk,
                        interrupt_event,
                    )
                )

            ai_response_active = False

            trace.record(
                "llm",
                "metrics",
                ttft_ms=llm_result[
                    "ttft_ms"
                ],
                first_chunk_ms=llm_result[
                    "first_chunk_ms"
                ],
                total_ms=llm_result[
                    "total_ms"
                ],
                interrupted=llm_result[
                    "interrupted"
                ],
            )

            # -------------------------------------------------
            # LLM interruption
            # -------------------------------------------------

            if llm_result[
                "interrupted"
            ]:

                trace.record(
                    "llm",
                    "interrupted",
                )

                await websocket.send_json(
                    {
                        "type": (
                            "ai_response_interrupted"
                        )
                    }
                )

                await websocket.send_json(
                    {
                        "type": "agent_trace",
                        **trace.get_trace(),
                    }
                )

                return

            # -------------------------------------------------
            # Empty LLM response protection
            # -------------------------------------------------

            if not llm_result[
                "response"
            ].strip():

                trace.record(
                    "llm",
                    "empty_response",
                )

                await websocket.send_json(
                    {
                        "type": "agent_trace",
                        **trace.get_trace(),
                    }
                )

                return

            await websocket.send_json(
                {
                    "type": "llm_completed",
                    "response": llm_result[
                        "response"
                    ],
                    "ttft_ms": llm_result[
                        "ttft_ms"
                    ],
                    "first_chunk_ms": (
                        llm_result[
                            "first_chunk_ms"
                        ]
                    ),
                    "total_ms": llm_result[
                        "total_ms"
                    ],
                    "speech_chunk_count": len(
                        llm_result[
                            "speech_chunks"
                        ]
                    ),
                }
            )

            # =================================================
            # Response Chunking
            # =================================================

            with trace.stage(
                "response_chunking"
            ):

                speech_chunks = (
                    llm_result[
                        "speech_chunks"
                    ]
                )

            trace.record(
                "response_chunking",
                "result",
                chunk_count=len(
                    speech_chunks
                ),
                chunks=[
                    {
                        "chunk_number": index
                        + 1,
                        "text": chunk,
                    }
                    for index, chunk in enumerate(
                        speech_chunks
                    )
                ],
            )

            # =================================================
            # TTS
            # =================================================

            await websocket.send_json(
                {
                    "type": (
                        "audio_response_start"
                    ),
                    "chunk_count": len(
                        speech_chunks
                    ),
                }
            )

            for index, speech_chunk in enumerate(
                speech_chunks
            ):

                # ---------------------------------------------
                # Barge-in check before TTS
                # ---------------------------------------------

                if interrupt_event.is_set():

                    trace.record(
                        "tts",
                        "cancelled",
                        chunk_number=index
                        + 1,
                        reason="barge_in",
                    )

                    await websocket.send_json(
                        {
                            "type": (
                                "tts_cancelled"
                            ),
                            "chunk_number": (
                                index + 1
                            ),
                        }
                    )

                    break

                # ---------------------------------------------
                # TTS
                # ---------------------------------------------

                output_filename = (
                    f"voice_response_"
                    f"{int(time.time() * 1000)}_"
                    f"{index + 1}.wav"
                )

                trace_tts_start = (
                    time.perf_counter()
                )

                tts_result = (
                    await asyncio.to_thread(
                        tts_service.synthesize,
                        speech_chunk,
                        output_filename,
                        interrupt_event,
                    )
                )

                tts_elapsed_ms = round(
                    (
                        time.perf_counter()
                        - trace_tts_start
                    )
                    * 1000,
                    2,
                )

                trace.record(
                    "tts",
                    "chunk_completed",
                    chunk_number=index + 1,
                    text=speech_chunk,
                    status=tts_result[
                        "status"
                    ],
                    tts_latency_ms=tts_result[
                        "tts_latency_ms"
                    ],
                    measured_elapsed_ms=(
                        tts_elapsed_ms
                    ),
                )

                # ---------------------------------------------
                # TTS cancelled
                # ---------------------------------------------

                if (
                    tts_result[
                        "status"
                    ]
                    == "cancelled"
                ):

                    await websocket.send_json(
                        {
                            "type": (
                                "tts_cancelled"
                            ),
                            "chunk_number": (
                                index + 1
                            ),
                        }
                    )

                    break

                # ---------------------------------------------
                # Send generated audio
                # ---------------------------------------------

                audio_path = tts_result[
                    "audio_path"
                ]

                if audio_path:

                    audio_file = Path(
                        audio_path
                    )

                    if audio_file.exists():

                        audio_bytes = (
                            audio_file.read_bytes()
                        )

                        await websocket.send_json(
                            {
                                "type": (
                                    "audio_response_chunk"
                                ),
                                "chunk_number": (
                                    index + 1
                                ),
                                "tts_latency_ms": (
                                    tts_result[
                                        "tts_latency_ms"
                                    ]
                                ),
                                "audio_size_bytes": (
                                    len(
                                        audio_bytes
                                    )
                                ),
                            }
                        )

                        # Send binary WAV audio.
                        await websocket.send_bytes(
                            audio_bytes
                        )

            # =================================================
            # Trace
            # =================================================

            trace.record(
                "voice",
                "completed",
            )

            await websocket.send_json(
                {
                    "type": "agent_trace",
                    **trace.get_trace(),
                }
            )

            await websocket.send_json(
                {
                    "type": (
                        "ai_response_finished"
                    )
                }
            )

        except Exception as exc:

            ai_response_active = False

            print(
                "[WebSocket] Voice turn error:",
                repr(exc),
            )

            trace.record(
                "voice",
                "error",
                error=str(exc),
            )

            try:

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(
                            exc
                        ),
                    }
                )

                await websocket.send_json(
                    {
                        "type": "agent_trace",
                        **trace.get_trace(),
                    }
                )

            except Exception:
                pass

        finally:

            ai_response_active = False

            if temp_path:

                try:

                    if os.path.exists(
                        temp_path
                    ):

                        os.remove(
                            temp_path
                        )

                except Exception:
                    pass

    # =========================================================
    # WebSocket message loop
    # =========================================================

    try:

        while True:

            message = (
                await websocket.receive()
            )

            # =================================================
            # Text message
            # =================================================

            if "text" in message:

                text = message[
                    "text"
                ]

                if not text:
                    continue

                try:

                    data = json.loads(
                        text
                    )

                except json.JSONDecodeError:

                    data = {
                        "type": text
                    }

                message_type = data.get(
                    "type"
                )

                # ---------------------------------------------
                # Start microphone audio
                # ---------------------------------------------

                if (
                    message_type
                    == "start_audio"
                ):

                    audio_chunks = []

                    total_audio_bytes = 0

                    chunk_number = 0

                    expecting_final_audio = (
                        False
                    )

                    interrupt_event.clear()

                    await websocket.send_json(
                        {
                            "type": (
                                "audio_stream_started"
                            )
                        }
                    )

                    print(
                        "[WebSocket] "
                        "Audio stream started."
                    )

                # ---------------------------------------------
                # Prepare final audio
                # ---------------------------------------------

                elif (
                    message_type
                    == "prepare_final_audio"
                ):

                    expecting_final_audio = (
                        True
                    )

                    final_audio_mime_type = (
                        data.get(
                            "mime_type",
                            "audio/webm",
                        )
                    )

                    await websocket.send_json(
                        {
                            "type": (
                                "ready_for_final_audio"
                            )
                        }
                    )

                    print(
                        "[WebSocket] "
                        "Ready for final audio."
                    )

                # ---------------------------------------------
                # Explicit interruption
                # ---------------------------------------------

                elif (
                    message_type
                    == "interrupt"
                ):

                    print(
                        "[WebSocket] "
                        "Interrupt command received."
                    )

                    interrupt_event.set()

                    await websocket.send_json(
                        {
                            "type": (
                                "interrupt_acknowledged"
                            )
                        }
                    )

                    if ai_response_active:

                        await websocket.send_json(
                            {
                                "type": (
                                    "ai_response_interrupted"
                                )
                            }
                        )

                # ---------------------------------------------
                # Close session
                # ---------------------------------------------

                elif (
                    message_type
                    == "close"
                ):

                    print(
                        "[WebSocket] "
                        "Close command received."
                    )

                    break

                # ---------------------------------------------
                # Unknown text message
                # ---------------------------------------------

                else:

                    print(
                        "[WebSocket] "
                        f"Unknown message type: "
                        f"{message_type}"
                    )

            # =================================================
            # Binary audio
            # =================================================

            elif (
                "bytes" in message
                and message["bytes"]
                is not None
            ):

                binary_data = message[
                    "bytes"
                ]

                # ---------------------------------------------
                # Final complete recording
                # ---------------------------------------------

                if expecting_final_audio:

                    expecting_final_audio = (
                        False
                    )

                    final_audio_size = len(
                        binary_data
                    )

                    print(
                        "[WebSocket] "
                        "Complete recording received: "
                        f"{final_audio_size} bytes"
                    )

                    await websocket.send_json(
                        {
                            "type": (
                                "final_audio_received"
                            ),
                            "audio_size_bytes": (
                                final_audio_size
                            ),
                        }
                    )

                    # IMPORTANT:
                    #
                    # A normal microphone chunk must NEVER
                    # set this event.
                    #
                    # We clear it before starting a new
                    # voice turn so the LLM is not
                    # immediately interrupted.

                    interrupt_event.clear()

                    await process_voice_turn(
                        websocket=websocket,
                        audio_data=binary_data,
                        mime_type=(
                            final_audio_mime_type
                        ),
                        interrupt_event=(
                            interrupt_event
                        ),
                    )

                    continue

                # ---------------------------------------------
                # Normal live microphone chunk
                # ---------------------------------------------

                chunk_number += 1

                total_audio_bytes += len(
                    binary_data
                )

                audio_chunks.append(
                    binary_data
                )

                print(
                    "[WebSocket] "
                    f"Audio chunk #{chunk_number}: "
                    f"{len(binary_data)} bytes"
                )

                # IMPORTANT:
                #
                # DO NOT call:
                #
                #     interrupt_event.set()
                #
                # here.
                #
                # These are normal microphone chunks.
                # Setting the interrupt event here would cause
                # the LLM to immediately stop when the final
                # recording is processed.

                await websocket.send_json(
                    {
                        "type": (
                            "audio_chunk_received"
                        ),
                        "chunk_number": (
                            chunk_number
                        ),
                        "chunk_size_bytes": (
                            len(binary_data)
                        ),
                        "total_audio_bytes": (
                            total_audio_bytes
                        ),
                    }
                )

    except WebSocketDisconnect:

        print(
            "[WebSocket] "
            "Client disconnected."
        )

    except Exception as exc:

        print(
            "[WebSocket] "
            "Session error:",
            repr(exc),
        )

        try:

            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(
                        exc
                    ),
                }
            )

        except Exception:
            pass

    finally:

        print(
            "[WebSocket] "
            "Voice session closed."
        )