"""逐帧读取独立解码器的全部 RGB 字节，仅保留验收需要的采样帧。"""
import hashlib
import subprocess
import tempfile


def decode_rgb_frames(command, width, height, frames, sample_indices):
    """核对完整解码长度、退出状态和摘要，返回指定帧的像素字节。"""
    frame_bytes = width * height * 3
    samples, digest = {}, hashlib.sha256()
    with tempfile.TemporaryFile() as errors:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors) as process:
            try:
                for index in range(frames):
                    data = process.stdout.read(frame_bytes)
                    if len(data) != frame_bytes:
                        raise ValueError('decoded_length_mismatch')
                    digest.update(data)
                    if index in sample_indices:
                        samples[index] = data
                if process.stdout.read(1):
                    raise ValueError('decoded_length_mismatch')
                if process.wait(timeout=120):
                    raise RuntimeError('decoder_failed')
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()
                process.stdout.close()
    return {'byteCount': frame_bytes * frames, 'sha256': digest.hexdigest(), 'samples': samples}
