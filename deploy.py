import re
import os
import sys
import markdown
import shutil
import base64
from typing import Optional

from create_data import create_db

def copyf(src: str, tgt: str) -> None:
    """Copy a file from src to tgt."""
    try:
        print(f"Copying {src} -> {tgt}")
        shutil.copyfile(src, tgt)
    except FileNotFoundError as e:
        print(f"Error copying {src}: {e}")

def copytree(src: str, tgt: str) -> None:
    """Copy a directory from src to tgt."""
    try:
        print(f"Copying directory {src} -> {tgt}")
        shutil.copytree(src, tgt)
    except FileNotFoundError as e:
        print(f"Error copying directory {src}: {e}")
    except FileExistsError as e:
        print(f"Directory {tgt} already exists: {e}")

def get_ver() -> Optional[str]:
    """Extract the version number from the first line of Changelog.md."""
    try:
        with open('Changelog.md', 'r', encoding='utf-8') as f:
            first = f.readline().strip()
        ver = first.split(': v')[-1]
        return ver
    except Exception as e:
        print(f"Error reading version: {e}")
        return None

def make_manual() -> str:
    """Convert README.md to HTML and include header and footer."""
    try:
        with open("README.md", "r", encoding="utf-8") as input_file:
            text = input_file.read()
            md = markdown.Markdown(extensions=['toc'])
            html = md.convert(text)

        with open("manual.html", "w", encoding="utf-8") as output_file:
            for part in ['header.html', 'footer.html']:
                with open(part, 'r', encoding='utf-8') as f:
                    output_file.write(f.read())
            output_file.write(html)
        return html
    except Exception as e:
        print(f"Error creating manual: {e}")
        return ""

def embed_service_worker(version: str) -> None:
    """Embed version number into sw.js and write to sw_deploy.js."""
    try:
        with open("sw.js", "r", encoding="utf-8") as f, open("sw_deploy.js", "w", encoding="utf-8") as out:
            content = f.read().replace('VERSION', version)
            out.write(content)
    except Exception as e:
        print(f"Error embedding service worker: {e}")

def png_encode(path: str) -> str:
    """Encode a PNG file to a base64 string."""
    try:
        with open(path, 'rb') as f:
            png = f.read()
            b64png = base64.b64encode(png).decode()
        return f'data:image/png;base64,{b64png}'
    except Exception as e:
        print(f"Error encoding PNG: {e}")
        return ""

def embed(manual: str, version: str) -> None:
    """Embed scripts and images as base64, and replace version placeholders in the HTML template."""
    script_pattern = re.compile(r'^<script src="(.*)"></script>')
    version_pattern = re.compile(r'.*Settings \((version)\).*')
    urlpng_pattern = re.compile(r'^(.*)url\(([a-z0-9_\-]*\.png)\)(.*)$')
    urlpng2_pattern = re.compile(r'^(.*<img.*)src="([a-z0-9_\-\/]*\.png)"(.*)$')

    try:
        with open("astrohopper.html", "r", encoding="utf-8") as f, open("astrohopper_deploy.html", "w", encoding="utf-8") as out:
            for line in f:
                m = script_pattern.match(line)
                v = version_pattern.match(line)
                u = urlpng_pattern.match(line)
                u2 = urlpng2_pattern.match(line)

                if m:
                    with open(m.group(1), "r", encoding="utf-8") as inline:
                        inline_content = inline.read()
                        out.write('<script>\n')
                        out.write(inline_content)
                        out.write('</script>\n')
                elif v:
                    out.write(line.replace('version', version))
                elif u or u2:
                    pat = '%surl(%s)%s\n' if u else '%ssrc="%s"%s\n'
                    match = u if u else u2
                    b64png = png_encode(match.group(2))
                    new_line = pat % (match.group(1), b64png, match.group(3))
                    out.write(new_line)
                elif line.strip() == 'MANUAL':
                    out.write(manual)
                else:
                    out.write(line)
    except Exception as e:
        print(f"Error embedding: {e}")

def deploy_files(target: str) -> None:
    """Copy final deployment files and the images directory to the target directory."""
    if not os.path.exists(target):
        os.makedirs(target)

    files_to_copy = ['astrohopper_deploy.html', 'sw_deploy.js', 'LICENSE', 'COPYING.md', 'manual.html', 'manifest.json']
    for file_name in files_to_copy:
        try:
            copyf(file_name, os.path.join(target, file_name))
        except Exception as e:
            print(f"Error copying {file_name}: {e}")
    
    # Copy the images directory
    try:
        copytree('icons', os.path.join(target, 'icons'))
    except Exception as e:
        print(f"Error copying images directory: {e}")

def main() -> None:
    """Main function to orchestrate the deployment process."""
    create_db()
    ver = get_ver()
    if not ver:
        print("Version could not be determined.")
        return

    man = make_manual()
    embed(man, ver)
    embed_service_worker(ver)

    target_dir = sys.argv[1] if len(sys.argv) > 1 else '_deploy'
    deploy_files(target_dir)

if __name__ == "__main__":
    main()
