"""
CLI principal de Scribe
"""

import click
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .transcriber import transcribe_audio
from .diarizer import diarize_audio
from .proofer import add_confidence_markers
from .exporters import export_json, export_srt, export_txt, export_docx

console = Console()

VALID_FORMATS = ["json", "srt", "txt", "docx"]
VALID_MODELS = ["tiny", "base", "small", "medium", "large"]
VALID_LANGUAGES = ["auto", "es", "en", "fr", "de", "it", "pt", "zh", "ja", "ko"]


@click.group(invoke_without_command=True)
@click.argument("audio_file", required=False, type=click.Path(exists=True))
@click.option("--speakers", "-s", default="auto", help="Número de speakers ('auto' o número)")
@click.option("--lang", "-l", default="auto", help="Idioma (es, en, auto)")
@click.option("--model", "-m", default="small", type=click.Choice(VALID_MODELS), help="Modelo Whisper")
@click.option("--format", "-f", "formats", default="json", help="Formatos de salida (json,srt,txt,docx)")
@click.option("--output", "-o", default=None, help="Nombre archivo de salida")
@click.option("--proofread", "-p", is_flag=True, help="Marcar segmentos con baja confianza")
@click.version_option(version=__version__)
@click.pass_context
def main(ctx, audio_file, speakers, lang, model, formats, output, proofread):
    """
    Scribe - Transcripción de audio con detección de speakers

    Ejemplo:
        scribe entrevista.mp3 --speakers 2 --lang es
    """
    if ctx.invoked_subcommand is not None:
        return

    if audio_file is None:
        click.echo(ctx.get_help())
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
    console.print(f"  Proofread: [cyan]{'Sí' if proofread else 'No'}[/cyan]\n")

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

        # 4. Exportar
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


@main.command()
def list_models():
    """Lista los modelos disponibles de Whisper"""
    console.print("\n[bold]Modelos disponibles:[/bold]\n")

    models_info = [
        ("tiny", "39 MB", "Más rápido, menor precisión"),
        ("base", "140 MB", "Balance básico"),
        ("small", "460 MB", "Recomendado para la mayoría"),
        ("medium", "1.5 GB", "Alta precisión"),
        ("large", "3 GB", "Máxima precisión, más lento"),
    ]

    for name, size, desc in models_info:
        console.print(f"  [cyan]{name:8}[/cyan] ({size:8}) - {desc}")

    console.print()


@main.command()
@click.argument("model_name", type=click.Choice(VALID_MODELS))
def download(model_name):
    """Descarga un modelo de Whisper"""
    import whisper

    console.print(f"\n[cyan]Descargando modelo '{model_name}'...[/cyan]\n")

    try:
        whisper.load_model(model_name)
        console.print(f"[green]Modelo '{model_name}' descargado correctamente![/green]\n")
    except Exception as e:
        console.print(f"[red]Error al descargar: {e}[/red]\n")


if __name__ == "__main__":
    main()
