from pathlib import Path
import tempfile
import unittest
from PIL import Image
import text_diagram as builder
import render_diagrams as exporter


class DiagramTests(unittest.TestCase):
    def test_example_is_current_and_rectangular(self):
        source = Path(__file__).resolve().parents[1] / 'examples/workflow.xml'
        target, drawings = builder._load(source)
        document = (source.parent / target).read_text()
        self.assertEqual(builder._render(document, drawings), document)
        self.assertEqual(len({len(line) for line in drawings['workflow'].lines}), 1)

    def test_row_connectors_and_padding(self):
        left = builder._box('left', ['a', 'b'], 8)
        right = builder._box('right', ['c'], 9)
        drawing = builder._beside([left, right], gap=2, links={(0, 1): '--'})
        self.assertEqual(len({len(line) for line in drawing.lines}), 1)
        self.assertIn('\N{NO-BREAK SPACE}', drawing.lines[0])
        self.assertIn('--', drawing.lines[1])

    def test_multiline_connector_groups(self):
        drawing = builder._place_lines(12, {1: ['▲ left', '│'], 9: ['│', '▼']})
        self.assertEqual(drawing.render(), ' ▲ left  │\n │       ▼')

    def test_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError, 'needs width'):
            builder._box('small', ['does not fit'], 4)

    def test_placement_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            builder._place_line(10, {0: 'abc', 2: 'def'})

    def test_target_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'input.xml'
            source.write_text('<diagrams target="../outside.md"/>')
            with self.assertRaisesRegex(ValueError, 'leaves the target root'):
                builder._main([str(source)])

    def test_dark_light_and_custom_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'input.md'
            source.write_text('# Example\n```text\n+----+\n| hi |\n+----+\n```\n')
            for name, options, background, ink in [
                ('dark', [], (16, 18, 20), (237, 237, 237)),
                ('light', ['--theme', 'light'], (255, 255, 255), (0, 0, 0)),
                ('custom', ['--background', '#112233', '--foreground', '#abcdef'],
                 (17, 34, 51), (171, 205, 239)),
            ]:
                output = Path(temp) / name
                exporter.main([str(source), '--output-dir', str(output), *options])
                with Image.open(output / '01-example.png') as image:
                    self.assertEqual(image.getpixel((0, 0)), background)
                    self.assertTrue(any(color == ink for count, color in image.getcolors(image.width * image.height)))

    def test_code_is_not_exported(self):
        self.assertEqual(exporter._diagrams('```python\n"+--+"\n```'), [])


if __name__ == '__main__':
    unittest.main()
