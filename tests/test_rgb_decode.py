"""完整流式解码的长度、像素采样与失败边界。"""
import sys
import unittest
from rgb_decode import decode_rgb_frames


class RgbDecodeTests(unittest.TestCase):
    def command(self, size, code=0):
        return [sys.executable, '-I', '-B', '-c',
                f'import sys;sys.stdout.buffer.write(bytes(range({size})));sys.exit({code})']

    def test_reads_all_frames_and_retains_selected_pixels(self):
        value = decode_rgb_frames(self.command(18), 2, 1, 3, (0, 2))
        self.assertEqual(value['byteCount'], 18)
        self.assertEqual(value['samples'], {0: bytes(range(6)), 2: bytes(range(12, 18))})
        self.assertEqual(len(value['sha256']), 64)

    def test_truncated_last_frame_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'decoded_length_mismatch'):
            decode_rgb_frames(self.command(17), 2, 1, 3, (0,))

    def test_extra_frame_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'decoded_length_mismatch'):
            decode_rgb_frames(self.command(19), 2, 1, 3, (0,))

    def test_decoder_failure_is_not_counted_as_success(self):
        with self.assertRaisesRegex(RuntimeError, 'decoder_failed'):
            decode_rgb_frames(self.command(18, 1), 2, 1, 3, (0,))
