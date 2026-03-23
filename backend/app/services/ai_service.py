import os
import logging
import asyncio
import assemblyai as aai
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import get_settings

logger = logging.getLogger("ai_service")
settings = get_settings()

# Initialize AssemblyAI with the API key from settings
aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY

class AIService:
    """
    AI Service using AssemblyAI for Cloud STT and LangChain (OpenAI) 
    for Hierarchical Summarization with EXTENSIVE DEBUG LOGGING.
    """

    @classmethod
    async def transcribe_audio(cls, audio_path: str) -> str:
        """Transcribe audio using AssemblyAI Cloud STT via direct REST API Call with full transcript logging."""
        logger.info(f"🎤 [DEBUG] STARTING TRANSCRIPTION: {audio_path}")
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found at: {audio_path}")

            import requests

            base_url = "https://api.assemblyai.com"
            headers = {"authorization": settings.ASSEMBLY_AI_API_KEY}

            # 1. Upload Local File
            logger.info("📡 [DEBUG] Uploading file to AssemblyAI...")
            def _upload():
                with open(audio_path, "rb") as f:
                    response = requests.post(f"{base_url}/v2/upload", headers=headers, data=f)
                    response.raise_for_status()
                    return response.json()["upload_url"]
            audio_url = await asyncio.to_thread(_upload)

            # 2. Trigger Transcription
            logger.info("📡 [DEBUG] Starting transcription task with language detection & advanced models...")
            data = {
                "audio_url": audio_url,
                "language_detection": True,
                "speech_models": ["universal-3-pro", "universal-2"],
                "speaker_labels": True,
                "punctuate": True,
                "format_text": True
            }
            def _start_transcription():
                response = requests.post(f"{base_url}/v2/transcript", json=data, headers=headers)
                response.raise_for_status()
                return response.json()['id']
            transcript_id = await asyncio.to_thread(_start_transcription)

            # 3. Poll for Completion
            polling_endpoint = f"{base_url}/v2/transcript/{transcript_id}"
            logger.info("⏳ [DEBUG] Polling for completion...")
            
            while True:
                def _poll():
                    response = requests.get(polling_endpoint, headers=headers)
                    response.raise_for_status()
                    return response.json()
                result = await asyncio.to_thread(_poll)
                
                status = result['status']
                if status == 'completed':
                    break
                elif status == 'error':
                    error_msg = result.get('error', 'Unknown Error')
                    if "no spoken audio" in error_msg.lower():
                        logger.warning("⚠️ [DEBUG] No speech detected in the audio file.")
                        return "No speech detected in this recording."
                    raise Exception(f"AssemblyAI Error: {error_msg}")
                
                logger.info(f"⏳ [DEBUG] AssemblyAI Status: {status}...")
                await asyncio.sleep(3)

            # 4. Process Result
            formatted_text = ""
            utterances = result.get('utterances', [])
            
            if utterances:
                logger.info(f"✅ [DEBUG] Transcription SUCCESS! Word count: {len(result.get('text', '').split())}")
                for utterance in utterances:
                    line = f"Speaker {utterance.get('speaker', 'A')}: {utterance.get('text', '')}"
                    formatted_text += line + "\n"
                    # Log every line so the user can see it in terminal
                    logger.info(f"📝 [TRANSCRIPT LINE] {line}")
            else:
                formatted_text = result.get('text', '')
                logger.info(f"✅ [DEBUG] Transcription SUCCESS! Word count: {len(formatted_text.split())}")
                logger.info(f"📝 [FULL TRANSCRIPT] {formatted_text}")

            return formatted_text
        except Exception as e:
            logger.error(f"❌ [DEBUG] Transcription failed: {e}")
            raise e

    @classmethod
    def _get_chunks(cls, text: str) -> List[str]:
        """Split text into manageable chunks (~3000 words each)."""
        words = text.split()
        chunk_size = 3000 
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    @classmethod
    async def summarize_transcript(cls, transcript: str) -> dict:
        """
        Hierarchical Summarization using LangChain with step-by-step logs.
        """
        word_count = len(transcript.split())
        logger.info(f"🧠 [DEBUG] STARTING SUMMARIZATION: {word_count} words total.")

        if not transcript or word_count < 20:
            logger.warning("⚠️ [DEBUG] Transcript is too small for AI extraction.")
            placeholder = "Transcript too short for meaningful AI extraction."
            return {
                "final_summary": placeholder,
                "formatted_summary": placeholder,
                "brief_summary": "N/A (Short Recording)",
                "chunk_summaries": [],
                "full_transcript": transcript
            }

        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL or "gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )

        # 1. Map Stage
        chunks = cls._get_chunks(transcript)
        logger.info(f"📊 [DEBUG] Chunking transcript into {len(chunks)} segments.")
        
        map_prompt = ChatPromptTemplate.from_template(
            "Extract significant discussion points, technical details, numbers, and decisions from this meeting segment. "
            "Focus on context and clarity while capturing essential information. "
            "Note: The transcript may contain Hindi, English, or Hinglish (mixed Hindi-English). "
            "Understand the context carefully and provide the output in professional English. "
            "\n\nSegment:\n{text}"
        )
        map_chain = map_prompt | llm | StrOutputParser()
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"🕒 [DEBUG] Summarizing Chunk {i+1}/{len(chunks)} (Input: {len(chunk.split())} words)...")
            summary = await map_chain.ainvoke({"text": chunk})
            chunk_summaries.append(summary)
            logger.info(f"✨ [CHUNK SUMMARY {i+1}] {summary[:200]}...")

        # 2. Reduce Stage (Formal MOM)
        logger.info("🔥 [DEBUG] Merging all segments into professional MOM...")
        
        reduce_prompt = ChatPromptTemplate.from_template(
            "Synthesize these meeting segment summaries into a professional, formal Minutes of Meeting (MOM) report in English. "
            "Ensure the report includes an Executive Summary, Decisions, and Action Items. "
            "Note: The original discussion might have been in Hindi/Hinglish, so ensure the English synthesis is clear and professional.\n\nSummaries:\n{summaries}"
        )
        reduce_chain = reduce_prompt | llm | StrOutputParser()
        
        combined_summaries_text = "\n\n".join(chunk_summaries)
        final_summary = await reduce_chain.ainvoke({"summaries": combined_summaries_text})

        # 3. Beautify Stage (Formatted Narrative Summary)
        logger.info("✨ [DEBUG] Generating well-formatted Final Summary report...")
        beautify_prompt = ChatPromptTemplate.from_template(
            "Create a COMPREHENSIVE STRATEGIC INTELLIGENCE BRIEFING report in English based on these meeting summaries. "
            "The discussion may have been in Hindi/Hinglish; focus on a rich, flowing narrative in professional English. "
            "\n\nCRITICAL INSTRUCTIONS: "
            "1. Aim for a balanced length (approx. 300-400 words total for the summary). "
            "2. Use Markdown headings (##) for each main topic. "
            "3. Use **Bold Text** for key decisions and milestones. "
            "4. Include a 'RECOMMENDATIONS & TASKS' section at the end. "
            "5. NO EMOJIS OR SYMBOLS: Strictly avoid using icons, checkboxes, or emojis; use simple dashes (-) for bullets. "
            "6. DO NOT use generic placeholders like [Your Name] or [Company Name]. "
            "7. Start directly with the overview or highlights."
            "\n\nSummaries:\n{summaries}"
        )
        beautify_chain = beautify_prompt | llm | StrOutputParser()
        formatted_summary = await beautify_chain.ainvoke({"summaries": combined_summaries_text})

        # 4. Dashboard Stage (Short Point-wise Summary)
        logger.info("📊 [DEBUG] Extracting concise dashboard summary points...")
        dashboard_prompt = ChatPromptTemplate.from_template(
            "Generate a BALANCED LONG-FORM DISCUSSION SUMMARY report for a dashboard view based on these summaries. "
            "Create a clear narrative of the conversation, structured with topic-wise sections. "
            "Include a section at the end titled 'AI SUGGESTED TASKS' listing instructions and responsible parties. "
            "\n\nCRITICAL INSTRUCTIONS: "
            "1. Return the response in PLAIN TEXT but use simple structure (headers, dashes for bullets). "
            "2. Capture nuance and context efficiently—aim for 250-400 words total. "
            "3. NO SYMBOLS: Do NOT use hashtags (#), bolding (**), italics (*), checkboxes ( [ ] ) or emojis. Use only simple text and dashes (-) for bullet points."
            "\n\nSummaries:\n{summaries}"
        )
        dashboard_chain = dashboard_prompt | llm | StrOutputParser()
        brief_summary = await dashboard_chain.ainvoke({"summaries": combined_summaries_text})

        logger.info("🏁 [DEBUG] AI Pipeline Finished Successfully.")
        return {
            "final_summary": final_summary,            # Formal MOM
            "formatted_summary": formatted_summary,    # Well-formatted synthesis
            "brief_summary": brief_summary,            # Dashboard points
            "chunk_summaries": chunk_summaries,        # Audit logs
            "full_transcript": transcript              # Verbatim
        }
