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
        """Transcribe audio using AssemblyAI Cloud STT with full transcript logging."""
        logger.info(f"🎤 [DEBUG] STARTING TRANSCRIPTION: {audio_path}")
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found at: {audio_path}")

            transcriber = aai.Transcriber()
            config = aai.TranscriptionConfig(
                speaker_labels=True,
                punctuate=True,
                format_text=True,
                speech_models=["universal-3-pro", "universal-2"],
                language_detection=True # Enable auto-detection for Hindi/Hinglish support
            )
            
            logger.info("📡 [DEBUG] Uploading and transcribing to AssemblyAI Cloud...")
            transcript = await asyncio.to_thread(transcriber.transcribe, audio_path, config)
            
            if transcript.status == aai.TranscriptStatus.error:
                error_msg = str(transcript.error)
                if "no spoken audio" in error_msg.lower():
                    logger.warning("⚠️ [DEBUG] No speech detected in the audio file.")
                    return "No speech detected in this recording."
                raise Exception(f"AssemblyAI Error: {error_msg}")

            logger.info(f"✅ [DEBUG] Transcription SUCCESS! Word count: {len(transcript.text.split())}")
            
            # Formating transcript with speaker labels
            formatted_text = ""
            if transcript.utterances:
                for utterance in transcript.utterances:
                    line = f"Speaker {utterance.speaker}: {utterance.text}"
                    formatted_text += line + "\n"
                    # Log every line so the user can see it in terminal
                    logger.info(f"📝 [TRANSCRIPT LINE] {line}")
            else:
                formatted_text = transcript.text
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
            "Extract highlights, decisions, and action items from this meeting segment. "
            "The transcript may contain Hindi, English, or Hinglish (mixed Hindi-English). "
            "Understand the context carefully and provide the summary in professional English. "
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
            "Create a well-formatted, easy-to-read final summary report in English based on these meeting summaries. "
            "The discussion may have been in Hindi/Hinglish; focus on a flowing narrative and key highlights in professional English that provide a complete picture:\n\nSummaries:\n{summaries}"
        )
        beautify_chain = beautify_prompt | llm | StrOutputParser()
        formatted_summary = await beautify_chain.ainvoke({"summaries": combined_summaries_text})

        # 4. Dashboard Stage (Short Point-wise Summary)
        logger.info("📊 [DEBUG] Extracting concise dashboard summary points...")
        dashboard_prompt = ChatPromptTemplate.from_template(
            "Extract 5-8 most critical, high-impact bullet points from these meeting summaries for a dashboard view. "
            "Keep them short, action-oriented, and easy to read at a glance:\n\nSummaries:\n{summaries}"
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
