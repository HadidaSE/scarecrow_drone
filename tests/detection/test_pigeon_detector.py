"""
Unit tests for PigeonDetector class.
Tests the detection system with mocked video stream and YOLO model.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'live_detection'))


class TestDetectionConfig:
    """Test suite for DetectionConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        from detect import DetectionConfig

        config = DetectionConfig()

        assert config.confidence_threshold == 0.5
        assert config.frame_width == 640
        assert config.frame_height == 480
        assert config.save_detections is True
        assert config.save_all_frames is False

    def test_custom_config(self):
        """Test custom configuration values."""
        from detect import DetectionConfig

        config = DetectionConfig(
            confidence_threshold=0.7,
            frame_width=1280,
            frame_height=720,
            flight_id=5
        )

        assert config.confidence_threshold == 0.7
        assert config.frame_width == 1280
        assert config.frame_height == 720
        assert config.flight_id == 5


class TestDetectionStats:
    """Test suite for DetectionStats dataclass."""

    def test_default_stats(self):
        """Test default statistics values."""
        from detect import DetectionStats

        stats = DetectionStats()

        assert stats.frames_received == 0
        assert stats.frames_processed == 0
        assert stats.detections_count == 0
        assert stats.total_pigeons == 0

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        from detect import DetectionStats
        import time

        stats = DetectionStats()
        stats.start_time = time.time() - 10  # Started 10 seconds ago

        elapsed = stats.get_elapsed_time()

        assert 9.9 <= elapsed <= 10.1  # Allow small margin

    def test_process_fps(self):
        """Test FPS calculation."""
        from detect import DetectionStats
        import time

        stats = DetectionStats()
        stats.start_time = time.time() - 10
        stats.frames_processed = 100

        fps = stats.get_process_fps()

        assert 9.9 <= fps <= 10.1  # ~10 FPS


class TestPigeonDetector:
    """Test suite for PigeonDetector class."""

    @pytest.fixture
    def detector(self):
        """Create PigeonDetector with default config."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(
            model_path="dummy_path.pt",
            sdp_file="dummy.sdp",
            save_detections=False,
            save_all_frames=False
        )
        return PigeonDetector(config)

    @pytest.fixture
    def sample_frame(self):
        """Create a sample video frame for testing."""
        return np.zeros((480, 640, 3), dtype=np.uint8)

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.model is None
        assert detector.ffmpeg_process is None
        assert detector.stats.frames_received == 0

    @patch('detect.Path')
    @patch('detect.YOLO')
    def test_load_model_success(self, mock_yolo, mock_path, detector):
        """Test successful model loading."""
        mock_path.return_value.exists.return_value = True
        mock_model = Mock()
        mock_yolo.return_value = mock_model

        result = detector.load_model()

        assert result is True
        assert detector.model is mock_model

    @patch('detect.Path')
    def test_load_model_file_not_found(self, mock_path, detector):
        """Test model loading when file doesn't exist."""
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        result = detector.load_model()

        assert result is False
        assert detector.model is None

    def test_should_process_frame_initial(self, detector):
        """Test frame processing timing on first call."""
        detector.last_process_time = 0.0

        result = detector.should_process_frame()

        assert result is True

    def test_should_process_frame_too_soon(self, detector):
        """Test frame processing timing when called too soon."""
        import time
        detector.last_process_time = time.time()  # Just set

        result = detector.should_process_frame()

        assert result is False  # Should skip

    def test_convert_frame(self, detector, sample_frame):
        """Test frame conversion from raw bytes."""
        raw_bytes = sample_frame.tobytes()

        result = detector.convert_frame(raw_bytes)

        assert result.shape == (480, 640, 3)
        assert result.dtype == np.uint8

    @patch('detect.YOLO')
    def test_detect_pigeons(self, mock_yolo_class, detector, sample_frame):
        """Test pigeon detection with mocked model."""
        # Setup mock model
        mock_box = Mock()
        mock_box.xyxy = [Mock()]
        mock_box.xyxy[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=[100, 100, 200, 200])))
        mock_box.conf = [Mock()]
        mock_box.conf[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=0.85)))

        mock_result = Mock()
        mock_result.boxes = [mock_box]

        mock_model = Mock()
        mock_model.return_value = [mock_result]
        detector.model = mock_model

        result = detector.detect_pigeons(sample_frame)

        assert len(result.boxes) == 1

    def test_detect_pigeons_no_model(self, detector, sample_frame):
        """Test detection raises error when model not loaded."""
        detector.model = None

        with pytest.raises(RuntimeError, match="Model not loaded"):
            detector.detect_pigeons(sample_frame)

    @patch('cv2.imwrite')
    def test_process_detection_no_pigeons(self, mock_imwrite, detector, sample_frame):
        """Test processing detection with no pigeons."""
        mock_result = Mock()
        mock_result.boxes = []

        count = detector.process_detection(mock_result, sample_frame)

        assert count == 0
        assert detector.stats.detections_count == 0
        mock_imwrite.assert_not_called()

    @patch('cv2.imwrite')
    def test_process_detection_with_pigeons(self, mock_imwrite, detector, sample_frame):
        """Test processing detection with pigeons found."""
        from pathlib import Path
        import tempfile

        # Use a real temp directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            detector.detections_dir = Path(tmpdir)
            detector.config.save_detections = True

            # Setup mock detection result
            mock_box = Mock()
            mock_box.xyxy = [Mock()]
            mock_box.xyxy[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=[100, 100, 200, 200])))
            mock_box.conf = [Mock()]
            mock_box.conf[0].cpu = Mock(return_value=Mock(numpy=Mock(return_value=0.85)))

            mock_result = Mock()
            mock_result.boxes = [mock_box]
            mock_result.plot = Mock(return_value=sample_frame)

            count = detector.process_detection(mock_result, sample_frame)

            assert count == 1
            assert detector.stats.detections_count == 1
            assert detector.stats.total_pigeons == 1

    def test_read_frame_no_process(self, detector):
        """Test reading frame when no ffmpeg process."""
        detector.ffmpeg_process = None

        result = detector.read_frame()

        assert result is None

    def test_read_frame_incomplete(self, detector, sample_frame):
        """Test reading frame with incomplete data."""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.read = Mock(return_value=b'incomplete')  # Wrong size
        detector.ffmpeg_process = mock_process

        result = detector.read_frame()

        assert result is None

    def test_read_frame_success(self, detector, sample_frame):
        """Test successful frame reading."""
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stdout.read = Mock(return_value=sample_frame.tobytes())
        detector.ffmpeg_process = mock_process

        result = detector.read_frame()

        assert result is not None
        assert len(result) == 640 * 480 * 3

    @patch('subprocess.Popen')
    def test_start_ffmpeg_stream_success(self, mock_popen, detector):
        """Test successful ffmpeg stream start."""
        mock_process = Mock()
        mock_popen.return_value = mock_process

        result = detector.start_ffmpeg_stream()

        assert result is True
        assert detector.ffmpeg_process is mock_process

    @patch('subprocess.Popen')
    def test_start_ffmpeg_stream_not_found(self, mock_popen, detector):
        """Test ffmpeg stream start when ffmpeg not found."""
        mock_popen.side_effect = FileNotFoundError()

        result = detector.start_ffmpeg_stream()

        assert result is False

    def test_cleanup(self, detector):
        """Test resource cleanup."""
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        detector.ffmpeg_process = mock_process

        detector.cleanup()

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    @patch('detect.Path')
    def test_setup_directories(self, mock_path, detector):
        """Test directory setup."""
        mock_frames_dir = Mock()
        mock_detections_dir = Mock()
        mock_path.side_effect = [mock_frames_dir, mock_detections_dir]

        detector.setup_directories()

        mock_frames_dir.mkdir.assert_called_once_with(exist_ok=True)
        mock_detections_dir.mkdir.assert_called_once_with(exist_ok=True)


class TestSignalHandling:
    """Test suite for signal handling."""

    def test_shutdown_signal_handler(self):
        """Test that signal handler sets shutdown flag."""
        from detect import signal_handler
        import detect

        # Reset flag
        detect.shutdown_requested = False

        signal_handler(None, None)

        assert detect.shutdown_requested is True


class TestVideoRecording:
    """Test suite for video recording functionality."""

    @pytest.fixture
    def detector_with_video(self):
        """Create detector with video recording enabled."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(
            model_path="dummy_path.pt",
            sdp_file="dummy.sdp",
            save_video=True,
            video_recordings_dir="test_recordings",
            flight_id=123
        )
        return PigeonDetector(config)

    @patch('subprocess.Popen')
    @patch('detect.Path')
    def test_start_stream_with_video_recording(self, mock_path, mock_popen, detector_with_video):
        """Test ffmpeg stream with video recording enabled."""
        mock_dir = Mock()
        mock_file_path = Mock()
        mock_file_path.absolute.return_value = "/abs/path/flight_123.mp4"
        mock_dir.__truediv__ = Mock(return_value=mock_file_path)
        mock_path.return_value = mock_dir

        mock_process = Mock()
        mock_popen.return_value = mock_process

        result = detector_with_video.start_ffmpeg_stream()

        assert result is True
        # Verify video recording path was set
        assert detector_with_video.video_file_relative is not None
        assert "recordings/" in detector_with_video.video_file_relative


class TestPrintMethods:
    """Test suite for print/output methods."""

    @pytest.fixture
    def detector(self):
        """Create PigeonDetector with default config."""
        from detect import PigeonDetector, DetectionConfig
        import time

        config = DetectionConfig(
            model_path="dummy_path.pt",
            sdp_file="dummy.sdp",
            save_detections=False
        )
        detector = PigeonDetector(config)
        detector.stats.start_time = time.time() - 60  # 60 seconds ago
        detector.stats.frames_received = 100
        detector.stats.frames_processed = 50
        detector.stats.detections_count = 5
        detector.stats.total_pigeons = 8
        return detector

    def test_print_stats(self, detector, capsys):
        """Test print_stats outputs correct format."""
        detector.print_stats()

        captured = capsys.readouterr()
        assert "Received:" in captured.out
        assert "Processed:" in captured.out
        assert "Process FPS:" in captured.out
        assert "Detections:" in captured.out

    def test_print_json_stats(self, detector, capsys):
        """Test print_json_stats outputs JSON format."""
        detector.print_json_stats()

        captured = capsys.readouterr()
        assert "DETECTION_RESULT_JSON:" in captured.out
        assert '"frames_processed":' in captured.out
        assert '"detections_count":' in captured.out

    def test_print_summary(self, detector, capsys):
        """Test print_summary outputs summary."""
        detector.print_summary()

        captured = capsys.readouterr()
        assert "SUMMARY" in captured.out
        assert "Duration:" in captured.out
        assert "Frames Received:" in captured.out
        assert "Frames Processed:" in captured.out
        assert "Frames with Pigeons:" in captured.out
        assert "Total Pigeons:" in captured.out

    def test_print_summary_no_frames(self, capsys):
        """Test print_summary with no frames processed."""
        from detect import PigeonDetector, DetectionConfig
        import time

        config = DetectionConfig()
        detector = PigeonDetector(config)
        detector.stats.start_time = time.time()
        detector.stats.frames_processed = 0

        detector.print_summary()

        captured = capsys.readouterr()
        assert "SUMMARY" in captured.out
        # Should not include FPS stats when no frames processed

    def test_print_summary_with_save_frames(self, detector, capsys):
        """Test print_summary mentions frame save directory."""
        detector.config.save_all_frames = True

        detector.print_summary()

        captured = capsys.readouterr()
        assert "frames" in captured.out.lower()

    def test_print_summary_with_detections(self, detector, capsys):
        """Test print_summary mentions detections directory."""
        detector.config.save_detections = True

        detector.print_summary()

        captured = capsys.readouterr()
        # Should mention detection images saved


class TestSaveFrame:
    """Test suite for save_frame method."""

    @pytest.fixture
    def detector(self):
        """Create detector for save frame tests."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(
            save_all_frames=True
        )
        return PigeonDetector(config)

    @pytest.fixture
    def sample_frame(self):
        """Create sample frame."""
        return np.zeros((480, 640, 3), dtype=np.uint8)

    @patch('cv2.imwrite')
    def test_save_frame_enabled(self, mock_imwrite, detector, sample_frame):
        """Test save_frame when enabled."""
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            detector.frames_dir = Path(tmpdir)
            detector.stats.frames_processed = 42

            detector.save_frame(sample_frame)

            mock_imwrite.assert_called_once()
            call_args = mock_imwrite.call_args[0]
            assert "frame_000042" in call_args[0]

    def test_save_frame_disabled(self, sample_frame):
        """Test save_frame when disabled."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(save_all_frames=False)
        detector = PigeonDetector(config)

        # Should not raise even with no frames_dir set
        detector.save_frame(sample_frame)


class TestCleanupWithVideo:
    """Test suite for cleanup with video recording."""

    @pytest.fixture
    def detector_with_video(self):
        """Create detector with video recording."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(
            save_video=True,
            video_recordings_dir="test_recordings"
        )
        return PigeonDetector(config)

    @patch('time.sleep')
    def test_cleanup_with_video_exists(self, mock_sleep, detector_with_video, capsys):
        """Test cleanup when video file exists."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock video file
            video_path = Path(tmpdir) / "test_video.mp4"
            video_path.write_bytes(b"fake video content" * 1000)

            detector_with_video.video_file_path = video_path
            mock_process = Mock()
            mock_process.terminate = Mock()
            mock_process.wait = Mock()
            detector_with_video.ffmpeg_process = mock_process

            detector_with_video.cleanup()

            captured = capsys.readouterr()
            assert "[VIDEO] Recording saved:" in captured.out

    @patch('time.sleep')
    def test_cleanup_with_video_not_exists(self, mock_sleep, detector_with_video, capsys):
        """Test cleanup when video file doesn't exist."""
        from pathlib import Path

        detector_with_video.video_file_path = Path("/nonexistent/video.mp4")
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        detector_with_video.ffmpeg_process = mock_process

        detector_with_video.cleanup()

        captured = capsys.readouterr()
        assert "[WARNING] Video file does not exist" in captured.out

    def test_cleanup_no_video(self):
        """Test cleanup without video recording."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(save_video=False)
        detector = PigeonDetector(config)
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        detector.ffmpeg_process = mock_process

        # Should not raise
        detector.cleanup()


class TestMainFunction:
    """Test suite for main() entry point."""

    @patch('detect.PigeonDetector')
    @patch('argparse.ArgumentParser')
    def test_main_with_args(self, mock_argparser, mock_detector_class):
        """Test main function parses arguments."""
        import detect

        # Setup mock args
        mock_args = Mock()
        mock_args.stream = "test.sdp"
        mock_args.flight_id = 123
        mock_args.save_detections = True
        mock_args.save_all_frames = False
        mock_args.save_video = True
        mock_args.confidence = 0.7

        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_argparser.return_value = mock_parser

        mock_detector = Mock()
        mock_detector.run = Mock()
        mock_detector_class.return_value = mock_detector

        # Reset shutdown flag
        detect.shutdown_requested = False

        detect.main()

        mock_detector.run.assert_called_once()

    @patch('detect.PigeonDetector')
    @patch('argparse.ArgumentParser')
    def test_main_default_args(self, mock_argparser, mock_detector_class):
        """Test main function with default arguments."""
        import detect

        # Setup mock args with all None/False
        mock_args = Mock()
        mock_args.stream = None
        mock_args.flight_id = None
        mock_args.save_detections = False
        mock_args.save_all_frames = False
        mock_args.save_video = False
        mock_args.confidence = None

        mock_parser = Mock()
        mock_parser.parse_args.return_value = mock_args
        mock_argparser.return_value = mock_parser

        mock_detector = Mock()
        mock_detector.run = Mock()
        mock_detector_class.return_value = mock_detector

        detect.shutdown_requested = False

        detect.main()

        mock_detector.run.assert_called_once()


class TestRunMethod:
    """Test suite for the run() method main loop."""

    @pytest.fixture
    def detector(self):
        """Create detector for run tests."""
        from detect import PigeonDetector, DetectionConfig

        config = DetectionConfig(
            model_path="dummy.pt",
            sdp_file="dummy.sdp",
            save_detections=False,
            save_all_frames=False,
            stats_interval=2
        )
        return PigeonDetector(config)

    @patch('signal.signal')
    def test_run_model_load_fails(self, mock_signal, detector, capsys):
        """Test run exits early when model fails to load."""
        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=False):

            detector.run()

            captured = capsys.readouterr()
            assert "PIGEON DETECTION SYSTEM" in captured.out

    @patch('signal.signal')
    def test_run_ffmpeg_fails(self, mock_signal, detector, capsys):
        """Test run exits early when ffmpeg fails to start."""
        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=False):

            detector.run()

            captured = capsys.readouterr()
            # Model loads successfully before ffmpeg fails
            assert "PIGEON DETECTION SYSTEM" in captured.out

    @patch('signal.signal')
    def test_run_stream_ends(self, mock_signal, detector, capsys):
        """Test run handles stream ending."""
        import detect

        # Reset shutdown flag
        detect.shutdown_requested = False

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', return_value=None), \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.run()

            captured = capsys.readouterr()
            assert "Stream ended" in captured.out or "Waiting for stream" in captured.out

    @patch('signal.signal')
    def test_run_shutdown_requested(self, mock_signal, detector, capsys):
        """Test run handles shutdown signal."""
        import detect
        import time

        # Simulate shutdown after first frame
        call_count = [0]
        def read_frame_side_effect():
            call_count[0] += 1
            if call_count[0] > 1:
                detect.shutdown_requested = True
                return None
            return np.zeros((480, 640, 3), dtype=np.uint8).tobytes()

        detect.shutdown_requested = False

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', side_effect=read_frame_side_effect), \
             patch.object(detector, 'should_process_frame', return_value=False), \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.run()

    @patch('signal.signal')
    def test_run_processes_frame(self, mock_signal, detector, capsys):
        """Test run processes frames correctly."""
        import detect
        import time

        # Return 2 frames then end
        frame_data = np.zeros((480, 640, 3), dtype=np.uint8).tobytes()
        frames = [frame_data, frame_data, None]
        frame_idx = [0]

        def read_frame_side_effect():
            result = frames[frame_idx[0]] if frame_idx[0] < len(frames) else None
            frame_idx[0] += 1
            return result

        mock_result = Mock()
        mock_result.boxes = []

        detect.shutdown_requested = False

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', side_effect=read_frame_side_effect), \
             patch.object(detector, 'should_process_frame', return_value=True), \
             patch.object(detector, 'detect_pigeons', return_value=mock_result), \
             patch.object(detector, 'process_detection', return_value=0), \
             patch.object(detector, 'print_json_stats'), \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.stats.start_time = time.time()
            detector.run()

            # Should have processed frames
            assert detector.stats.frames_received > 0

    @patch('signal.signal')
    def test_run_prints_stats_interval(self, mock_signal, detector, capsys):
        """Test run prints stats at configured interval."""
        import detect
        import time

        # Return enough frames to trigger stats print
        frame_data = np.zeros((480, 640, 3), dtype=np.uint8).tobytes()
        frames = [frame_data] * 5 + [None]
        frame_idx = [0]

        def read_frame_side_effect():
            result = frames[frame_idx[0]] if frame_idx[0] < len(frames) else None
            frame_idx[0] += 1
            return result

        mock_result = Mock()
        mock_result.boxes = []

        detect.shutdown_requested = False
        detector.config.stats_interval = 2  # Print every 2 frames

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', side_effect=read_frame_side_effect), \
             patch.object(detector, 'should_process_frame', return_value=True), \
             patch.object(detector, 'detect_pigeons', return_value=mock_result), \
             patch.object(detector, 'process_detection', return_value=0), \
             patch.object(detector, 'print_json_stats'), \
             patch.object(detector, 'print_stats') as mock_print_stats, \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.stats.start_time = time.time()
            detector.run()

            # Should have called print_stats at interval
            assert mock_print_stats.called

    @patch('signal.signal')
    def test_run_keyboard_interrupt(self, mock_signal, detector, capsys):
        """Test run handles KeyboardInterrupt."""
        import detect

        detect.shutdown_requested = False

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', side_effect=KeyboardInterrupt), \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.run()

            captured = capsys.readouterr()
            assert "Stopping" in captured.out

    @patch('signal.signal')
    def test_run_first_frame_message(self, mock_signal, detector, capsys):
        """Test run prints first frame message."""
        import detect
        import time

        frame_data = np.zeros((480, 640, 3), dtype=np.uint8).tobytes()
        frames = [frame_data, None]
        frame_idx = [0]

        def read_frame_side_effect():
            result = frames[frame_idx[0]] if frame_idx[0] < len(frames) else None
            frame_idx[0] += 1
            return result

        detect.shutdown_requested = False

        with patch.object(detector, 'setup_directories'), \
             patch.object(detector, 'load_model', return_value=True), \
             patch.object(detector, 'start_ffmpeg_stream', return_value=True), \
             patch.object(detector, 'read_frame', side_effect=read_frame_side_effect), \
             patch.object(detector, 'should_process_frame', return_value=False), \
             patch.object(detector, 'cleanup'), \
             patch.object(detector, 'print_summary'):

            detector.stats.start_time = time.time()
            detector.first_frame = True
            detector.run()

            captured = capsys.readouterr()
            assert "First frame received" in captured.out
