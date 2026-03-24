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
    async def summarize_transcript(cls, transcript: str, agenda: str = "No specific agenda provided.") -> dict:
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
            "Extract significant discussion points, technical details, material numbers, decisions, **Action Items (Tasks)**, and **Recommended Next Steps** from this meeting segment. "
            "Use the provided Official Agenda as your strategic context. "
            "\n\nOFFICIAL AGENDA:\n{agenda}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Focus on context and clarity while capturing essential information linked to the agenda.\n"
            "2. Distinguish between 'Material Strategic Figures' (e.g., Budgets, Assets, Final Investment Amounts) and 'Conversational Noise' (e.g., minor calculation errors, trial numbers, or process-level arguments).\n"
            "3. ACTION ITEMS: Explicitly extract any task discussed, whether assigned or unassigned. Label unassigned tasks as 'General Action Items'.\n"
            "4. RECOMMENDATIONS: Capture any suggestions or proposed strategic steps mentioned.\n"
            "5. If a calculation error (like 400g vs 500g) is discussed, only note that 'calculations were reconciled' if relevant. Do NOT list the specific intermediate numbers of the error.\n"
            "6. Note: The transcript may contain Hindi, English, or Hinglish. Provide output in professional English.\n"
            "\n\nSegment:\n{text}"
        )
        map_chain = map_prompt | llm | StrOutputParser()
        
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"🕒 [DEBUG] Summarizing Chunk {i+1}/{len(chunks)} (Input: {len(chunk.split())} words)...")
            summary = await map_chain.ainvoke({"text": chunk, "agenda": agenda})
            chunk_summaries.append(summary)
            logger.info(f"✨ [CHUNK SUMMARY {i+1}] {summary[:200]}...")

        # 2. Reduce Stage (Formal MOM)
        logger.info("🔥 [DEBUG] Merging all segments into professional MOM...")
        
        reduce_prompt = ChatPromptTemplate.from_template(
            "Synthesize these segment summaries into a professional, formal MOM report in English. "
            "Ensure the report includes an Executive Summary, Decisions, **Strict Action items**, and **Recommended Tasks**. "
            "Refer to the Official Agenda for structure: \n{agenda}\n\n"
            "Note: Original discussion might be Hindi/Hinglish. English synthesis must be clear and professional.\n\nSummaries:\n{summaries}"
        )
        reduce_chain = reduce_prompt | llm | StrOutputParser()
        
        combined_summaries_text = "\n\n".join(chunk_summaries)
        final_summary = await reduce_chain.ainvoke({"summaries": combined_summaries_text, "agenda": agenda})

        # 3. Beautify Stage (Formatted Narrative Summary)
        logger.info("✨ [DEBUG] Generating well-formatted Final Summary report...")
        beautify_prompt = ChatPromptTemplate.from_template(
            "Create a COMPREHENSIVE STRATEGIC INTELLIGENCE BRIEFING report in English. "
            "Use the provided Official Agenda to organize the report: \n{agenda}\n\n"
            "CRITICAL FORMATTING INSTRUCTIONS:\n"
            "1. HIERARCHY: Every major topic/section must start with a **BOLD AND UPPERCASE HEADER** followed by a colon (e.g., **AI INFRASTRUCTURE INVESTMENT PROPOSAL:**). \n"
            "2. FORMATTED BULLETS: All descriptions, details, and metrics under each header must be in normal (non-bold) bullet points (-).\n"
            "3. MANDATORY SECTION: You MUST include a final section titled **RECOMMENDED TASKS & NEXT STEPS:** with specific actionable items.\n"
            "4. STRATEGIC MAGNITUDE: Preserve high-value metrics (e.g., ₹2 Crores) but discard minor conversational noise. Focus on the CONCLUSION.\n"
            "5. NO EMOJIS: Use simple dashes (-) for bullets.\n"
            "6. NO PARAGRAPHS: Keep the briefing crisp and point-wise where possible.\n"
            "\n\nSummaries:\n{summaries}"
        )
        beautify_chain = beautify_prompt | llm | StrOutputParser()
        formatted_summary = await beautify_chain.ainvoke({"summaries": combined_summaries_text, "agenda": agenda})

        # 4. Dashboard Stage (Balanced Narrative Summary for UI Autofill)
        logger.info("📊 [DEBUG] Extracting balanced dashboard summary points...")
        dashboard_prompt = ChatPromptTemplate.from_template(
            "Generate a HIGH-IMPACT, POINT-WISE PROFESSIONAL SUMMARY for a web dashboard. "
            "Reference Official Agenda: {agenda}\n\n"
            "CRITICAL FORMATTING INSTRUCTIONS:\n"
            "1. BOLD HEADERS: Every main debate/topic/section header must be **BOLD AND UPPERCASE** (e.g., **CONFORMANCE & AUDIT:**, **FINANCIAL ALLOCATION:**).\n"
            "2. MANDATORY SECTIONS: You MUST explicitly include **DECISIONS MADE:** and **RECOMMENDED TASKS:** sections.\n"
            "3. NORMAL BULLETS: All descriptive points under headers must be plain text bullet points (-). DO NOT bold the bullet point text itself.\n"
            "4. POINT-WISE ONLY: No paragraphs. Use a structured list for every topic.\n"
            "5. STRATEGIC MAGNITUDE: Record final agreed-upon figures and high-value metrics (e.g. ₹2 Crores). Discard process-level noise.\n"
            "6. NO HALLUCINATION: Only list items that were EXPLICITLY discussed.\n"
            "7. NO EMOJIS: Use only plain text and simple dashes (-).\n"
            "\n\nSummaries:\n{summaries}"
        )
        dashboard_chain = dashboard_prompt | llm | StrOutputParser()
        brief_summary = await dashboard_chain.ainvoke({"summaries": combined_summaries_text, "agenda": agenda})

        logger.info("🏁 [DEBUG] AI Pipeline Finished Successfully.")
        return {
            "final_summary": final_summary,            # Formal MOM
            "formatted_summary": formatted_summary,    # Well-formatted synthesis
            "brief_summary": brief_summary,            # Dashboard points
            "chunk_summaries": chunk_summaries,        # Audit logs
            "full_transcript": transcript              # Verbatim
        }
