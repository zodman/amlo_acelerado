import asyncclick as click
import os
from anyio import run_process as run
import subprocess
import json

click.anyio_backend = "asyncio"


async def get_youtube_desc(youtube_url):
    r = await run(f"youtube-dl -j '{youtube_url}'")
    res = json.loads(r.stdout)
    desc = res.get("description")
    file_ = res.get("_filename")
    title = res.get("fulltitle")
    return desc, file_, title

async def speedup(filename, out_filename):
    await run(f'ffmpeg -i {filename}  -filter:v "setpts=PTS/2" -filter:a "atempo=2" -y "{out_filename}" ')

async def upload(filename, title, description):
    r= await run([
        'youtube-upload',
        '--client-secrets=client_secrets.json',
        f'-t "{title}"',
        f'--description="{description}"',
        '--privacy=unlisted',
        f'{filename}'
    ], check=False, stderr= subprocess.STDOUT)
    print(r.stdout.decode("utf-8"))
    

@click.group()
async def cli():
    pass

@cli.command(name="down")
@click.argument("youtube_url")
async def download_youtube(youtube_url):
    click.echo("get youtubedl")
    desc, filename, title = await get_youtube_desc(youtube_url)
    r = await run(f"youtube-dl -f 18 '{youtube_url}'")
    if os.path.exists(filename): 
        click.echo("executing jumpcutter")
        if os.path.exists("TEMP"):
            await run("rm TEMP -rf")
        new_filename = filename.replace(" ", "_")
        if not os.path.exists(f'{new_filename.replace(".mp4", "_ALTERED.mp4")}'):
            await run(f"mv '{filename}' {new_filename}")
            cmd = f'python jumpcutter.py --input_file "{new_filename}"'
            # print(cmd)
            r = await run(cmd, stderr=subprocess.STDOUT, check=False)
            r.check_returncode()
            print(r.stdout.decode("utf-8"))
        new_filename = new_filename.replace(".mp4", "_ALTERED.mp4")
        click.echo("finished jumpcutter")
        out_filename = new_filename.replace("_ALTERED.mp4", "_OUT.mp4")
        if not os.path.exists(out_filename):
            click.echo("speedup video")
            await speedup(new_filename, out_filename)
        click.echo("finish speedup and uploading")
        await upload(out_filename, title, desc)
        click.echo("finish upload")

    else:
        print("not exists")





if __name__ == "__main__":
    cli()
