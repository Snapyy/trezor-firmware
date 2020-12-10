from micropython import const

from trezor import ui

from ...constants import (
    TEXT_HEADER_HEIGHT,
    TEXT_LINE_HEIGHT,
    TEXT_LINE_HEIGHT_HALF,
    TEXT_MARGIN_LEFT,
    TEXT_MAX_LINES,
)

if False:
    from typing import List, Union, Dict, Optional

    TextContent = Union[str, int]

# needs to be different from all colors and font ids
BR = const(-256)
BR_HALF = const(-257)


class TextBase(ui.Component):
    def __init__(self) -> None:
        super().__init__()
        self.content = []  # type: List[TextContent]
        self.header_text = None  # type: Optional[str]
        self.max_lines = TEXT_MAX_LINES

    def normal(self, *content: TextContent) -> None:
        self.content.append(ui.NORMAL)
        self.content.extend(content)

    def bold(self, *content: TextContent) -> None:
        self.content.append(ui.BOLD)
        self.content.extend(content)

    def mono(self, *content: TextContent) -> None:
        self.content.append(ui.MONO)
        self.content.extend(content)

    def br(self) -> None:
        self.content.append(BR)

    def br_half(self) -> None:
        self.content.append(BR_HALF)

    def format_parametrized(
        self,
        format_string: str,
        *params: str,
        font: int = ui.NORMAL,
        param_font: int = ui.BOLD,
    ) -> None:
        self.content.append(font)
        param_iter = iter(params)
        for line in format_string.split("\n"):
            if "{}" in line:
                param = next(param_iter)
                l, r = line.split("{}", 1)
                if l:
                    self.content.append(l.rstrip())
                self.content.append(param_font)
                self.content.append(param)
                self.content.append(font)
                if r:
                    self.content.append(r.lstrip())
            else:
                self.content.append(line)
            self.content.append(BR)

    def count_lines(self) -> int:
        # TODO: more accurately count lines that are not pre-broken?
        line_count = 0
        item_on_this_line = False
        for item in self.content:
            if isinstance(item, str):
                item_on_this_line = True
            if item == BR:
                line_count += 1
                item_on_this_line = False

        if item_on_this_line:
            # trailing line did not have BR
            line_count += 1

        return line_count

    def on_render(self) -> None:
        pass

    if __debug__:

        def read_content(self) -> List[str]:
            lines = [w for w in self.content if isinstance(w, str)]
            header_text = [self.header_text] if self.header_text is not None else []
            return (
                header_text + lines[: self.max_lines]
            )  # FIXME elements of content do not always map to lines


def render_text(
    words: List[TextContent],
    new_lines: bool,
    max_lines: int,
    font: int = ui.NORMAL,
    fg: int = ui.FG,
    bg: int = ui.BG,
    offset_x: int = TEXT_MARGIN_LEFT,
    offset_y: int = TEXT_HEADER_HEIGHT + TEXT_LINE_HEIGHT,
    offset_x_max: int = ui.WIDTH,
) -> None:
    # initial rendering state
    INITIAL_OFFSET_X = offset_x
    offset_y_max = TEXT_HEADER_HEIGHT + (TEXT_LINE_HEIGHT * max_lines)

    FONTS = (ui.NORMAL, ui.BOLD, ui.MONO)

    # sizes of common glyphs
    SPACE = ui.display.text_width(" ", font)
    DASH = ui.display.text_width("-", ui.BOLD)
    ELLIPSIS = ui.display.text_width("...", ui.BOLD)

    for word_index, word in enumerate(words):
        has_next_word = word_index < len(words) - 1

        if isinstance(word, int):
            if word is BR or word is BR_HALF:
                # line break or half-line break
                if offset_y > offset_y_max:
                    ui.display.text(offset_x, offset_y, "...", ui.BOLD, ui.GREY, bg)
                    return
                offset_x = INITIAL_OFFSET_X
                offset_y += TEXT_LINE_HEIGHT if word is BR else TEXT_LINE_HEIGHT_HALF
            elif word in FONTS:
                # change of font style
                font = word
            else:
                # change of foreground color
                fg = word
            continue

        width = ui.display.text_width(word, font)

        while offset_x + width > offset_x_max or (
            has_next_word and offset_y >= offset_y_max
        ):
            beginning_of_line = offset_x == INITIAL_OFFSET_X
            word_fits_in_one_line = width < (offset_x_max - INITIAL_OFFSET_X)
            if (
                offset_y < offset_y_max
                and word_fits_in_one_line
                and not beginning_of_line
            ):
                # line break
                offset_x = INITIAL_OFFSET_X
                offset_y += TEXT_LINE_HEIGHT
                break
            # word split
            if offset_y < offset_y_max:
                split = "-"
                splitw = DASH
            else:
                split = "..."
                splitw = ELLIPSIS
            # find span that fits
            for index in range(len(word) - 1, 0, -1):
                letter = word[index]
                width -= ui.display.text_width(letter, font)
                if offset_x + width + splitw < offset_x_max:
                    break
            else:
                index = 0
            span = word[:index]
            # render word span
            ui.display.text(offset_x, offset_y, span, font, fg, bg)
            ui.display.text(offset_x + width, offset_y, split, ui.BOLD, ui.GREY, bg)
            # line break
            if offset_y >= offset_y_max:
                return
            offset_x = INITIAL_OFFSET_X
            offset_y += TEXT_LINE_HEIGHT
            # continue with the rest
            word = word[index:]
            width = ui.display.text_width(word, font)

        # render word
        ui.display.text(offset_x, offset_y, word, font, fg, bg)

        if new_lines and has_next_word:
            # line break
            if offset_y >= offset_y_max:
                ui.display.text(offset_x, offset_y, "...", ui.BOLD, ui.GREY, bg)
                return
            offset_x = INITIAL_OFFSET_X
            offset_y += TEXT_LINE_HEIGHT
        else:
            # shift cursor
            offset_x += width
            offset_x += SPACE
