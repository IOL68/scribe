"""
Scribe UI - Interfaz gráfica para transcripción de audio
"""

import gradio as gr
from pathlib import Path
import tempfile
import shutil

from scribe.transcriber import transcribe_audio
from scribe.diarizer import diarize_audio
from scribe.exporters.docx_exporter import export_docx
from scribe.exporters.json_exporter import export_json
from scribe.exporters.srt_exporter import export_srt
from scribe.exporters.txt_exporter import export_txt
from scribe.error_reporter import report_error


def transcribe(audio_file, speakers, lang, format_type, model):
    """Procesa el audio y retorna el archivo transcrito."""

    if audio_file is None:
        return None, "❌ Por favor selecciona un archivo de audio"

    try:
        audio_path = Path(audio_file)

        # Transcribir
        result = transcribe_audio(
            str(audio_path),
            model=model,
            language=lang if lang != "auto" else None
        )

        # Diarizar
        num_speakers = None if speakers == 0 else int(speakers)
        result = diarize_audio(str(audio_path), result, num_speakers=num_speakers)

        # Exportar
        output_dir = tempfile.mkdtemp()
        output_name = audio_path.stem

        if format_type == "docx":
            output_path = Path(output_dir) / f"{output_name}.docx"
            export_docx(result, output_path)
        elif format_type == "json":
            output_path = Path(output_dir) / f"{output_name}.json"
            export_json(result, output_path)
        elif format_type == "srt":
            output_path = Path(output_dir) / f"{output_name}.srt"
            export_srt(result, output_path)
        else:  # txt
            output_path = Path(output_dir) / f"{output_name}.txt"
            export_txt(result, output_path)

        # Resumen
        duration = result.get("duration", 0)
        num_segments = len(result.get("segments", []))
        detected_speakers = result.get("speakers", 0)

        summary = f"""✅ Transcripción completada

📊 **Resumen:**
- Duración: {int(duration // 60)}:{int(duration % 60):02d}
- Segmentos: {num_segments}
- Speakers detectados: {detected_speakers}
- Formato: {format_type.upper()}
"""

        return str(output_path), summary

    except Exception as e:
        # Reportar error automáticamente a GitHub
        report_error(e, context="UI - transcribiendo audio")
        return None, f"❌ Error: {str(e)}\n\n_(Error reportado automáticamente)_"


def create_ui():
    """Crea la interfaz de Gradio."""

    with gr.Blocks(
        title="Scribe - Transcripción de Audio",
        theme=gr.themes.Soft()
    ) as app:

        gr.Markdown("""
        # 🎙️ Scribe
        ### Transcripción de audio con detección de speakers

        100% local - tus audios nunca salen de tu computadora.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                audio_input = gr.Audio(
                    label="Audio",
                    type="filepath",
                    sources=["upload", "microphone"]
                )

                with gr.Row():
                    speakers_input = gr.Number(
                        label="Speakers",
                        value=2,
                        minimum=0,
                        maximum=10,
                        step=1,
                        info="0 = auto-detectar"
                    )

                    lang_input = gr.Dropdown(
                        label="Idioma",
                        choices=["auto", "es", "en"],
                        value="auto"
                    )

                with gr.Row():
                    format_input = gr.Dropdown(
                        label="Formato",
                        choices=["docx", "json", "srt", "txt"],
                        value="docx"
                    )

                    model_input = gr.Dropdown(
                        label="Modelo",
                        choices=["tiny", "base", "small", "medium", "large"],
                        value="small",
                        info="Mayor = más preciso pero lento"
                    )

                transcribe_btn = gr.Button(
                    "🎯 Transcribir",
                    variant="primary",
                    size="lg"
                )

            with gr.Column(scale=1):
                output_file = gr.File(
                    label="📄 Archivo generado"
                )

                output_summary = gr.Markdown(
                    label="Resumen"
                )

        transcribe_btn.click(
            fn=transcribe,
            inputs=[audio_input, speakers_input, lang_input, format_input, model_input],
            outputs=[output_file, output_summary]
        )

        gr.Markdown("""
        ---
        **Tip:** Arrastra y suelta tu archivo de audio, o graba directamente con el micrófono.
        """)

    return app


def main():
    """Inicia la UI."""
    app = create_ui()
    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    main()
