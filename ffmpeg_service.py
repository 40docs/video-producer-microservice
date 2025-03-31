import os
import subprocess
import shutil

def produce_video(output_name="final_output"):
    image_dir = "assets/images"
    audio_dir = "assets/audio"
    output_dir = "assets/temp"
    output_final_dir = "outputs"
    bumper_path_in = os.path.abspath("assets/bumpers/bumper_in.mp4")
    bumper_path_out = os.path.abspath("assets/bumpers/bumper_out.mp4")
    final_output = os.path.join(output_final_dir, f"{output_name}.mp4")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_final_dir, exist_ok=True)

    def get_audio_duration(audio_path):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        return float(result.stdout)

    def is_cbr(audio_file):
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'format=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        bitrate_info = result.stdout.decode().strip()
        return bool(bitrate_info)

    def convert_to_cbr(input_audio, output_audio):
        if is_cbr(input_audio):
            shutil.copy(input_audio, output_audio)
        else:
            subprocess.run([
                'ffmpeg', '-i', input_audio, '-b:a', '192k',
                '-ar', '48000', '-ac', '2', '-y', output_audio
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    images = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
    audios = sorted([f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav'))])

    for idx, (image, audio) in enumerate(zip(images, audios)):
        image_path = os.path.join(image_dir, image)
        audio_path = os.path.join(audio_dir, audio)
        output_video = os.path.join(output_dir, f"output_{idx+1:03d}.mp4")

        audio_duration = get_audio_duration(audio_path)

        ffmpeg_command = [
            'ffmpeg', '-y', '-i', image_path,
            '-i', audio_path,
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            '-t', str(audio_duration),
            output_video
        ]

        subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    filelist_path = os.path.join(output_dir, 'filelist.txt')
    with open(filelist_path, 'w') as f:
        if os.path.exists(bumper_path_in):
            f.write(f"file '{bumper_path_in}'\n")
        for idx in range(len(images)):
            part = os.path.abspath(os.path.join(output_dir, f"output_{idx+1:03d}.mp4"))
            if os.path.exists(part):
                f.write(f"file '{part}'\n")
        if os.path.exists(bumper_path_out):
            f.write(f"file '{bumper_path_out}'\n")

    concat_command = [
        'ffmpeg', '-loglevel', 'verbose', '-y', '-f', 'concat', '-safe', '0',
        '-i', filelist_path, '-c', 'copy', final_output
    ]
    subprocess.run(concat_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if os.path.exists(final_output):
        shutil.rmtree(output_dir, ignore_errors=True)
        return final_output
    else:
        raise RuntimeError("❌ Failed to create final video.")
