import unittest
from backend.camera.capture import VideoCaptureThread

class TestIPWebcamParsing(unittest.TestCase):
    def test_ip_webcam_parsing_raw_ip(self):
        v = VideoCaptureThread("192.168.1.50:8080")
        self.assertTrue(v.is_network_stream)
        self.assertEqual(v.parsed_source, "http://192.168.1.50:8080/video")

    def test_ip_webcam_parsing_with_http(self):
        v = VideoCaptureThread("http://192.168.1.50:8080")
        self.assertTrue(v.is_network_stream)
        self.assertEqual(v.parsed_source, "http://192.168.1.50:8080/video")

    def test_ip_webcam_parsing_with_existing_path(self):
        v = VideoCaptureThread("http://192.168.1.50:8080/video")
        self.assertTrue(v.is_network_stream)
        self.assertEqual(v.parsed_source, "http://192.168.1.50:8080/video")

    def test_ip_webcam_single_slash_typo(self):
        v = VideoCaptureThread("http:/192.168.1.50:8080/video")
        self.assertTrue(v.is_network_stream)
        self.assertEqual(v.parsed_source, "http://192.168.1.50:8080/video")

    def test_rtsp_stream(self):
        v = VideoCaptureThread("rtsp://192.168.1.50:8080/h264_pcm.sdp")
        self.assertTrue(v.is_network_stream)
        self.assertEqual(v.parsed_source, "rtsp://192.168.1.50:8080/h264_pcm.sdp")

    def test_webcam_index(self):
        v = VideoCaptureThread("0")
        self.assertTrue(v.is_webcam)
        self.assertEqual(v.parsed_source, 0)

    def test_demo_file(self):
        v = VideoCaptureThread("data/demo_videos/sample_border.mp4")
        self.assertTrue(v.is_file)
        self.assertEqual(v.parsed_source, "data/demo_videos/sample_border.mp4")

if __name__ == "__main__":
    unittest.main()
