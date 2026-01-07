"""
CLI principal de Scribe
"""

import click
import subprocess
import sys
import tempfile
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .transcriber import transcribe_audio
from .diarizer import diarize_audio
from .proofer import add_confidence_markers
from .separator import separate_by_diarization, cleanup_temp_files
from .comparator import compare_transcriptions
from .exporters import export_json, export_srt, export_txt, export_docx
from .error_reporter import report_error

console = Console()

VALID_FORMATS = ["json", "srt", "txt", "docx"]
VALID_MODELS = ["tiny", "base", "small", "medium", "large"]


def do_update(ctx, param, value):
    """Actualiza scribe a la última versión"""
    if not value or ctx.resilient_parsing:
        return
    console.print("[cyan]Actualizando Scribe...[/cyan]")
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/pipx", "install",
             "git+https://github.com/IOL68/scribe.git",
             "--python", "/opt/homebrew/bin/python3.11", "--force"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            console.print("[green]Scribe actualizado correctamente![/green]")
        else:
            console.print(f"[red]Error al actualizar:[/red] {result.stderr}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
    ctx.exit()


@click.command()
@click.argument("audio_file", type=click.Path(exists=True), required=False)
@click.option("--update", is_flag=True, callback=do_update, expose_value=False, is_eager=True, help="Actualizar a la última versión")
@click.option("--speakers", "-s", default="auto", help="Número de speakers ('auto' o número)")
@click.option("--lang", "-l", default="auto", help="Idioma (es, en, auto)")
@click.option("--model", "-m", default="small", type=click.Choice(VALID_MODELS), help="Modelo Whisper")
@click.option("--format", "-f", "formats", default="json", help="Formatos de salida (json,srt,txt,docx)")
@click.option("--output", "-o", default=None, help="Nombre archivo de salida")
@click.option("--proofread", "-p", is_flag=True, help="Marcar segmentos con baja confianza")
@click.option("--verify", "-v", is_flag=True, help="Verificar separando voces y comparando")
@click.version_option(version=__version__)
def main(audio_file, speakers, lang, model, formats, output, proofread, verify):
    """
    Scribe - Transcripción de audio con detección de speakers

    \b
    Ejemplo:
        scribe entrevista.mp3 --speakers 2 --lang es
        scribe --update  (actualizar a última versión)
    """
    if not audio_file:
        console.print("[red]Error: Debes especificar un archivo de audio.[/red]")
        console.print("Uso: scribe archivo.mp3 --format docx")
        console.print("     scribe --update  (para actualizar)")
        return

    audio_path = Path(audio_file)

    # Parsear formatos
    format_list = [f.strip().lower() for f in formats.split(",")]
    for fmt in format_list:
        if fmt not in VALID_FORMATS:
            console.print(f"[red]Error: Formato '{fmt}' no válido. Usa: {', '.join(VALID_FORMATS)}[/red]")
            return

    # Parsear speakers
    num_speakers = None if speakers == "auto" else int(speakers)

    # Nombre de salida
    output_base = output if output else audio_path.stem

    console.print(f"\n[bold blue]Scribe v{__version__}[/bold blue]\n")
    console.print(f"  Archivo: [cyan]{audio_path.name}[/cyan]")
    console.print(f"  Modelo: [cyan]{model}[/cyan]")
    console.print(f"  Idioma: [cyan]{lang}[/cyan]")
    console.print(f"  Speakers: [cyan]{speakers}[/cyan]")
    console.print(f"  Formatos: [cyan]{', '.join(format_list)}[/cyan]")
    console.print(f"  Proofread: [cyan]{'Sí' if proofread else 'No'}[/cyan]")
    console.print(f"  Verify: [cyan]{'Sí' if verify else 'No'}[/cyan]\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # 1. Transcribir
            task = progress.add_task("[cyan]Transcribiendo audio...", total=None)
            result = transcribe_audio(str(audio_path), model=model, language=lang if lang != "auto" else None)
            progress.update(task, completed=True, description="[green]Transcripción completada")

            # 2. Diarizar
            task = progress.add_task("[cyan]Detectando speakers...", total=None)
            result = diarize_audio(str(audio_path), result, num_speakers=num_speakers)
            progress.update(task, completed=True, description="[green]Speakers detectados")

            # 3. Proofread
            if proofread:
                task = progress.add_task("[cyan]Analizando confianza...", total=None)
                result = add_confidence_markers(result)
                progress.update(task, completed=True, description="[green]Análisis completado")

            # 4. Verificar (separar voces y comparar)
            temp_files = []
            if verify and num_speakers and num_speakers > 1:
                task = progress.add_task("[cyan]Separando voces...", total=None)

                # Crear directorio temporal
                temp_dir = tempfile.mkdtemp(prefix="scribe_verify_")

                # Separar audio por speaker usando diarización
                separated_paths = separate_by_diarization(
                    str(audio_path),
                    result["segments"],
                    num_speakers=num_speakers,
                    output_dir=temp_dir,
                )
                temp_files.extend(separated_paths)
                progress.update(task, completed=True, description="[green]Voces separadas")

                # Transcribir cada audio separado
                task = progress.add_task("[cyan]Transcribiendo voces separadas...", total=None)
                separated_transcriptions = []
                for sep_path in separated_paths:
                    sep_result = transcribe_audio(sep_path, model=model, language=lang if lang != "auto" else None)
                    separated_transcriptions.append(sep_result)
                progress.update(task, completed=True, description="[green]Voces transcritas")

                # Comparar transcripciones
                task = progress.add_task("[cyan]Comparando transcripciones...", total=None)
                result = compare_transcriptions(result, separated_transcriptions)
                progress.update(task, completed=True, description="[green]Verificación completada")

                # Limpiar archivos temporales
                cleanup_temp_files(temp_files)

            # 5. Exportar
            task = progress.add_task("[cyan]Exportando resultados...", total=None)

            output_dir = audio_path.parent
            exported_files = []

            for fmt in format_list:
                output_path = output_dir / f"{output_base}.{fmt}"

                if fmt == "json":
                    export_json(result, output_path)
                elif fmt == "srt":
                    export_srt(result, output_path)
                elif fmt == "txt":
                    export_txt(result, output_path)
                elif fmt == "docx":
                    export_docx(result, output_path)

                exported_files.append(output_path)

            progress.update(task, completed=True, description="[green]Exportación completada")

        console.print("\n[bold green]Listo![/bold green] Archivos generados:\n")
        for f in exported_files:
            console.print(f"  [cyan]{f}[/cyan]")
        console.print()

    except Exception as e:
        report_error(e, context="CLI - transcribiendo audio")
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Este error fue reportado automáticamente.[/dim]")


if __name__ == "__main__":
    main()
