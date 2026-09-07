import unittest
from tikdow.display import layout_for, clamp_position


class DisplayTests(unittest.TestCase):
    def test_resolution_and_dpi_matrix(self):
        for width, height in ((1920,1080), (2560,1440), (3840,2160)):
            for dpi in (96,120,144,168,192,240,288):
                with self.subTest(resolution=(width,height), dpi=dpi):
                    work_height = height - round(48*dpi/96)
                    scale, w, h = layout_for(width, work_height, dpi)
                    self.assertGreater(scale, 0)
                    self.assertLessEqual(scale, dpi/96)
                    self.assertLessEqual(w + round(32*dpi/96), width + 1)
                    self.assertLessEqual(h + round(80*dpi/96), work_height + 1)
                    self.assertAlmostEqual(w/h, 860/800, delta=.003)

    def test_4k_200_percent_is_double_full_hd_100(self):
        low = layout_for(1920,1032,96)
        high = layout_for(3840,2064,192)
        self.assertEqual(high, tuple(value*2 for value in low))

    def test_negative_monitor_and_offscreen_position(self):
        work=(-2560,0,0,1400)
        x,y=clamp_position(5000,5000,1290,1200,work,144)
        self.assertGreaterEqual(x,work[0])
        self.assertGreaterEqual(y,work[1])
        self.assertLessEqual(x+1290,work[2])
        self.assertLessEqual(y+1200,work[3])

    def test_repeated_scaling_has_no_accumulated_drift(self):
        expected=layout_for(1920,1032,96)
        for _ in range(10):
            layout_for(3840,2064,192)
            self.assertEqual(layout_for(1920,1032,96),expected)
