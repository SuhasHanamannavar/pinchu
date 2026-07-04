from enum import Enum
from math import sin, cos, pi
from PyQt5.QtCore import QRectF, QPointF, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QRadialGradient, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt


class CharacterState(Enum):
    IDLE = "idle"
    NOTICING = "noticing"
    PRESENTING = "presenting"
    PLEASED = "pleased"
    CONCERNED = "concerned"
    SLEEPY = "sleepy"
    EXCITED = "excited"
    LAUGHING = "laughing"
    THINKING = "thinking"
    SURPRISED = "surprised"
    PROUD = "proud"
    LISTENING = "listening"


def _ease_in_out(t):
    return t * t * (3 - 2 * t)


def _lerp(a, b, t):
    return a + (b - a) * t


class CharacterWidget(QWidget):
    clicked = pyqtSignal()
    W = 180
    H = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.W, self.H)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.state = CharacterState.IDLE
        self._t = 0.0
        self._bob_offset = 0.0
        self._ear_raise = 0.0
        self._eye_widen = 1.0
        self._arm_reach = 0.0
        self._bounce_phase = 0.0
        self._tilt = 0.0
        self._blink = 0
        self._caption = ""
        self._caption_alpha = 0.0
        self._sparkle_phase = 0.0
        self._yawn_progress = 0.0

        self._breath = 0.0
        self._look_x = 0.0
        self._look_y = 0.0
        self._look_target_x = 0.0
        self._look_target_y = 0.0
        self._look_timer = 0
        self._tail_wag = 0.0
        self._ear_twitch = 0.0
        self._blush_alpha = 0.0
        self._eyebrow_raise_l = 0.0
        self._eyebrow_raise_r = 0.0
        self._pupil_size = 5.0
        self._body_pulse = 0.0

        self._state_duration = 0
        self._state_timer = 0
        self._idle_skip = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

        self._transition_target = None
        self._transition_progress = 0.0

        self._cached_body_path = None
        self._cached_body_grad = None
        self._cached_glow_path = None
        self._cached_glow_grad = None
        self._cached_star_path = None
        self._cached_tail_path = None

    def set_state(self, state: CharacterState, caption: str = ""):
        if state != self.state:
            self._transition_target = state
            self._transition_progress = 0.0
        self.state = state
        self._caption = caption
        if caption:
            self._caption_alpha = 1.0
        self._state_timer = 0
        self._state_duration = {
            CharacterState.IDLE: 0, CharacterState.NOTICING: 50,
            CharacterState.PRESENTING: 80, CharacterState.PLEASED: 40,
            CharacterState.CONCERNED: 60, CharacterState.SLEEPY: 0,
            CharacterState.EXCITED: 50, CharacterState.LAUGHING: 45,
            CharacterState.THINKING: 55, CharacterState.SURPRISED: 35,
            CharacterState.PROUD: 50, CharacterState.LISTENING: 0,
        }.get(state, 50)

    def _tick(self):
        self._t += 0.05
        self._state_timer += 1
        dt = 0.05
        self._breath = sin(self._t * 1.2) * 0.02
        self._body_pulse = 0.5 + sin(self._t * 1.2) * 0.5

        is_idle = self.state in (CharacterState.IDLE, CharacterState.SLEEPY, CharacterState.LISTENING)
        if is_idle:
            self._idle_skip += 1
            if self._idle_skip % 5 != 0:
                return
        else:
            self._idle_skip = 0

        if self._transition_target and self._transition_progress < 1.0:
            self._transition_progress = min(1.0, self._transition_progress + dt * 3)

        self._look_timer += 1
        if self._look_timer > 120:
            self._look_timer = 0
            self._look_target_x = (sin(self._t * 0.7) * 6) if self._state_timer % 240 < 120 else 0
            self._look_target_y = (sin(self._t * 0.5 + 1) * 3) if self._state_timer % 300 < 150 else 0
        self._look_x += (self._look_target_x - self._look_x) * 0.05
        self._look_y += (self._look_target_y - self._look_y) * 0.05

        if self.state == CharacterState.IDLE:
            self._bob_offset = sin(self._t * 2.0) * 3
            self._ear_raise = sin(self._t * 0.8) * 1.5
            self._eye_widen = 1.0
            self._arm_reach = 0.0
            self._tilt = 0.0
            self._tail_wag = sin(self._t * 1.5) * 0.3
            self._blush_alpha *= 0.95
            self._eyebrow_raise_l = 0.0
            self._eyebrow_raise_r = 0.0
            self._pupil_size = 5.0
            if self._state_timer % 150 == 0:
                self._blink = 4
            if self._state_timer % 80 == 0:
                self._ear_twitch = 1.0

        elif self.state == CharacterState.NOTICING:
            p = min(1.0, self._state_timer / 20)
            ep = _ease_in_out(p)
            self._bob_offset = -2 + sin(self._t * 4.0) * 1
            self._ear_raise = ep * 14
            self._eye_widen = 1.0 + ep * 0.35
            self._arm_reach = ep * 0.2
            self._tilt = -3 * ep
            self._blush_alpha = _lerp(self._blush_alpha, 0.2, 0.05)
            self._eyebrow_raise_l = ep * 4
            self._eyebrow_raise_r = ep * 4
            self._pupil_size = 5.5

        elif self.state == CharacterState.LISTENING:
            p = min(1.0, self._state_timer / 15)
            self._bob_offset = sin(self._t * 2.5) * 2
            self._ear_raise = 2 + sin(self._t * 2.0) * 1.5
            self._eye_widen = 1.05
            self._arm_reach = 0.0
            self._tilt = -2 * p
            self._blush_alpha = _lerp(self._blush_alpha, 0.15, 0.05)
            self._eyebrow_raise_l = 1.5
            self._eyebrow_raise_r = 1.5
            self._pupil_size = 5.0

        elif self.state == CharacterState.PRESENTING:
            p = min(1.0, self._state_timer / 25)
            ep = _ease_in_out(p)
            self._bob_offset = -8 * ep + sin(self._t * 2.0) * 1
            self._ear_raise = ep * 12
            self._eye_widen = 1.0
            self._arm_reach = ep
            self._tilt = 0.0
            self._blush_alpha = _lerp(self._blush_alpha, 0.1, 0.03)
            self._eyebrow_raise_l = ep * 2
            self._eyebrow_raise_r = ep * 2
            self._pupil_size = 5.0

        elif self.state == CharacterState.THINKING:
            p = min(1.0, self._state_timer / 20)
            self._bob_offset = sin(self._t * 1.5) * 2
            self._ear_raise = 1 + sin(self._t * 1.0) * 2
            self._eye_widen = 0.9
            self._arm_reach = p * 0.3
            self._tilt = 5 * p
            self._blush_alpha = _lerp(self._blush_alpha, 0.0, 0.05)
            self._eyebrow_raise_l = 5 * p
            self._eyebrow_raise_r = 0.0
            self._pupil_size = 4.5

        elif self.state == CharacterState.SURPRISED:
            p = min(1.0, self._state_timer / 10)
            ep = _ease_in_out(p)
            self._bob_offset = -4 * ep
            self._ear_raise = 16 * ep
            self._eye_widen = 1.0 + ep * 0.5
            self._arm_reach = ep * 0.4
            self._tilt = 0.0
            self._blush_alpha = 0.0
            self._eyebrow_raise_l = 8 * ep
            self._eyebrow_raise_r = 8 * ep
            self._pupil_size = 4.0

        elif self.state == CharacterState.PROUD:
            p = min(1.0, self._state_timer / 20)
            ep = _ease_in_out(p)
            self._bob_offset = -6 * ep + sin(self._t * 2.0) * 1
            self._ear_raise = 4 + sin(self._t * 2.5) * 2
            self._eye_widen = 1.0
            self._arm_reach = 0.5 + sin(self._t * 2.0) * 0.15
            self._tilt = 0.0
            self._blush_alpha = _lerp(0.0, 0.3, ep)
            self._eyebrow_raise_l = 2
            self._eyebrow_raise_r = 2
            self._pupil_size = 5.0
            self._tail_wag = sin(self._t * 4.0) * 0.8

        elif self.state == CharacterState.PLEASED:
            self._bounce_phase += 0.06
            bp = abs(sin(self._bounce_phase))
            self._bob_offset = -bp * 8
            self._ear_raise = 2 + sin(self._t * 3.0) * 2.5
            self._eye_widen = 1.0
            self._arm_reach = 0.3 + sin(self._t * 3.0) * 0.1
            self._tilt = 0.0
            self._blush_alpha = _lerp(self._blush_alpha, 0.25, 0.05)
            self._eyebrow_raise_l = 0.0
            self._eyebrow_raise_r = 0.0
            self._pupil_size = 5.0
            self._tail_wag = sin(self._t * 5.0) * 0.6

        elif self.state == CharacterState.CONCERNED:
            self._bob_offset = sin(self._t * 1.5) * 2
            self._ear_raise = -6
            self._eye_widen = 0.82
            self._arm_reach = 0.0
            self._tilt = 5 * sin(self._t * 2.0)
            self._blush_alpha = 0.0
            self._eyebrow_raise_l = 0.0
            self._eyebrow_raise_r = 0.0
            self._pupil_size = 5.5
            self._tail_wag = 0.0

        elif self.state == CharacterState.SLEEPY:
            self._bob_offset = sin(self._t * 0.8) * 2
            self._ear_raise = -3
            self._eye_widen = 0.65
            self._arm_reach = 0.0
            self._tilt = sin(self._t * 0.5) * 2
            self._blush_alpha = 0.0
            self._eyebrow_raise_l = -1
            self._eyebrow_raise_r = -1
            self._pupil_size = 4.0
            self._tail_wag = 0.0
            if self._state_timer % 200 == 0:
                self._yawn_progress = 1.0

        elif self.state == CharacterState.EXCITED:
            self._bounce_phase += 0.12
            bp = abs(sin(self._bounce_phase))
            self._bob_offset = -bp * 14
            self._ear_raise = 6 + bp * 6
            self._eye_widen = 1.3
            self._arm_reach = 0.6 + sin(self._t * 5.0) * 0.25
            self._tilt = 0.0
            self._sparkle_phase += 0.1
            self._blush_alpha = _lerp(self._blush_alpha, 0.3, 0.05)
            self._eyebrow_raise_l = 4
            self._eyebrow_raise_r = 4
            self._pupil_size = 5.5
            self._tail_wag = sin(self._t * 6.0) * 1.0

        elif self.state == CharacterState.LAUGHING:
            self._bounce_phase += 0.1
            self._bob_offset = sin(self._bounce_phase * 2) * 6
            self._ear_raise = 3 + sin(self._t * 4.0) * 1
            self._eye_widen = 0.92
            self._arm_reach = 0.2 + sin(self._t * 4.0) * 0.1
            self._tilt = sin(self._bounce_phase) * 3
            self._blush_alpha = _lerp(self._blush_alpha, 0.35, 0.05)
            self._eyebrow_raise_l = 0.0
            self._eyebrow_raise_r = 0.0
            self._pupil_size = 5.0
            self._tail_wag = sin(self._t * 5.0) * 0.4

        if self._ear_twitch > 0:
            self._ear_twitch = max(0, self._ear_twitch - 0.05)
        if self._blink > 0:
            self._blink -= 1
        if self._yawn_progress > 0:
            self._yawn_progress = max(0, self._yawn_progress - 0.02)
        if self._state_duration > 0 and self._state_timer > self._state_duration:
            self.set_state(CharacterState.IDLE)
        if self._caption_alpha > 0 and self.state != CharacterState.PRESENTING:
            self._caption_alpha = max(0, self._caption_alpha - 0.005)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        cx, cy = self.W / 2, self.H / 2 + 15
        by = cy + self._bob_offset
        breath_offset = self._breath
        painter.save()
        painter.translate(cx, by + breath_offset * 4)
        painter.rotate(self._tilt)
        ps = 1.0 + self._breath * 0.5
        painter.scale(ps, ps)
        self._draw_tail(painter)
        self._draw_body(painter)
        self._draw_ears(painter)
        self._draw_arms(painter)
        self._draw_eyes(painter)
        self._draw_eyebrows(painter)
        self._draw_mouth(painter)
        painter.restore()
        self._draw_caption(painter, cx, by)

    def _draw_tail(self, p):
        if self._cached_tail_path is None:
            tail = QPainterPath()
            tail.moveTo(-8, 32)
            tail.quadTo(-14, 40, -20, 46)
            tail.quadTo(-24, 48, -18, 48)
            tail.quadTo(-8, 44, 0, 36)
            tail.closeSubpath()
            self._cached_tail_path = tail
        p.save()
        wag = self._tail_wag or sin(self._t * 1.5) * 0.2
        p.translate(0, 4)
        p.rotate(wag * 12)
        p.fillPath(self._cached_tail_path, QColor("#d0b0e4"))
        p.restore()

    def _draw_body(self, p):
        if self._cached_body_path is None:
            body = QPainterPath()
            body.addEllipse(QRectF(-45, -38, 90, 82))
            body.addEllipse(QRectF(-38, -8, 76, 68))
            self._cached_body_path = body
            grad = QRadialGradient(QPointF(0, -12), 50)
            grad.setColorAt(0, QColor("#ede0f8"))
            grad.setColorAt(0.5, QColor("#dcc4f0"))
            grad.setColorAt(1, QColor("#c4a3e0"))
            self._cached_body_grad = grad
            glow = QPainterPath()
            glow.addEllipse(QRectF(-32, -32, 24, 16))
            self._cached_glow_path = glow
            glow_grad = QRadialGradient(QPointF(0, -26), 20)
            glow_grad.setColorAt(0, QColor(255, 255, 255, 90))
            glow_grad.setColorAt(1, QColor(255, 255, 255, 0))
            self._cached_glow_grad = glow_grad
        p.fillPath(self._cached_body_path, self._cached_body_grad)
        p.setPen(Qt.NoPen)
        p.fillPath(self._cached_glow_path, self._cached_glow_grad)

    def _draw_ears(self, p):
        er = self._ear_raise
        twitch = self._ear_twitch * 0
        for side in (-1, 1):
            ear = QPainterPath()
            base_x, base_y = side * 36, -24
            tw = (twitch if side == 1 else -twitch)
            tip_x = base_x + side * 8 + tw * 2
            tip_y = base_y - 22 - er
            ear.moveTo(base_x - 7, base_y)
            ear.quadTo(base_x + side * 5, base_y - 10 - er * 0.5, tip_x, tip_y)
            ear.quadTo(base_x + side * 3, base_y - er * 0.3, base_x + 7, base_y)
            ear.closeSubpath()
            e_grad = QLinearGradient(base_x, base_y, tip_x, tip_y)
            e_grad.setColorAt(0, QColor("#d0b0e4"))
            e_grad.setColorAt(1, QColor("#e8d4f4"))
            p.fillPath(ear, e_grad)
            inner = QPainterPath()
            inner.moveTo(base_x - 3, base_y - 3)
            inner.quadTo(base_x + side * 4, base_y - 8 - er * 0.5, tip_x + side * 1, tip_y + 5)
            inner.quadTo(base_x + side * 1, base_y - er * 0.2, base_x + 3, base_y - 3)
            p.fillPath(inner, QColor("#f4e8fa"))

    def _draw_arms(self, p):
        reach = self._arm_reach
        for side in (-1, 1):
            arm = QPainterPath()
            sx, sy = side * 40, 6
            ex = side * (52 + reach * 24)
            ey = 18 + reach * 14
            arm.moveTo(sx, sy)
            arm.quadTo(side * 48, sy + 6 + reach * 14, ex, ey)
            arm.quadTo(side * 38, ey - 4, sx, sy)
            arm.closeSubpath()
            a_grad = QLinearGradient(sx, sy, ex, ey)
            a_grad.setColorAt(0, QColor("#dcc4f0"))
            a_grad.setColorAt(1, QColor("#c8a8dc"))
            p.fillPath(arm, a_grad)

    def _draw_eyebrows(self, p):
        for side in (-1, 1):
            raise_val = self._eyebrow_raise_l if side == -1 else self._eyebrow_raise_r
            bx = side * 12
            by = -22 - raise_val
            brow = QPainterPath()
            brow.moveTo(bx - 7, by)
            brow.lineTo(bx + 7, by - raise_val * 0.3)
            p.setPen(QPen(QColor("#4a2d5c"), 2.2, cap=Qt.RoundCap))
            p.drawPath(brow)
            p.setPen(Qt.NoPen)

    def _draw_eyes(self, p):
        ew = 16 * self._eye_widen
        eh = 18 if self._eye_widen > 1.1 else 16
        if self.state in (CharacterState.LAUGHING,):
            for side in (-1, 1):
                ex = side * 14
                ey = -10
                arc = QPainterPath()
                arc.moveTo(ex - 6, ey - 2)
                arc.quadTo(ex, ey - 8, ex + 6, ey - 2)
                p.setPen(QPen(QColor("#3d1f52"), 2.5, cap=Qt.RoundCap))
                p.drawPath(arc)
                p.setPen(Qt.NoPen)
                self._draw_blush(p, ex, ey)
            return
        for side in (-1, 1):
            ex = side * 14
            ey = -10
            if self.state == CharacterState.SLEEPY:
                white = QPainterPath()
                white.addEllipse(QRectF(ex - ew / 2, ey - eh / 4, ew, eh * 0.6))
                p.fillPath(white, QColor("#ffffff"))
                p.setPen(QPen(QColor("#d0e0d0"), 1))
                p.drawPath(white)
                p.setPen(Qt.NoPen)
                pupil_r = 4.0
                pupil = QPainterPath()
                pupil.addEllipse(QRectF(ex - pupil_r + self._look_x * 0.3, ey + 1 + self._look_y * 0.3, pupil_r * 2, pupil_r * 2))
                p.fillPath(pupil, QColor("#5c4a6a"))
                lid = QPainterPath()
                lid.moveTo(ex - ew / 2, ey - 2)
                lid.lineTo(ex + ew / 2, ey - 2)
                p.setPen(QPen(QColor("#8a7a9a"), 2.5, cap=Qt.RoundCap))
                p.drawPath(lid)
                p.setPen(Qt.NoPen)
                continue
            if self.state == CharacterState.SURPRISED:
                white = QPainterPath()
                white.addEllipse(QRectF(ex - ew / 2, ey - eh / 2, ew, eh))
                p.fillPath(white, QColor("#ffffff"))
                p.setPen(QPen(QColor("#d0d0d0"), 1.5))
                p.drawPath(white)
                p.setPen(Qt.NoPen)
                pupil_r = 4.0
                pupil = QPainterPath()
                pupil.addEllipse(QRectF(ex - pupil_r + self._look_x * 0.3, ey - pupil_r + self._look_y * 0.3, pupil_r * 2, pupil_r * 2))
                p.fillPath(pupil, QColor("#3d1f52"))
                hl_r = 2.0
                hl = QPainterPath()
                hl.addEllipse(QRectF(ex - 1 + self._look_x * 0.3, ey - 4 + self._look_y * 0.3, hl_r * 2, hl_r * 2))
                p.fillPath(hl, QColor(255, 255, 255, 220))
                continue
            white = QPainterPath()
            white.addEllipse(QRectF(ex - ew / 2, ey - eh / 2, ew, eh))
            p.fillPath(white, QColor("#ffffff"))
            p.setPen(QPen(QColor("#d0d0d0"), 1))
            p.drawPath(white)
            p.setPen(Qt.NoPen)
            if self._blink > 0:
                line = QPainterPath()
                line.moveTo(ex - ew / 2 + 2, ey)
                line.lineTo(ex + ew / 2 - 2, ey)
                p.setPen(QPen(QColor("#6b4c80"), 2.5, cap=Qt.RoundCap))
                p.drawPath(line)
                p.setPen(Qt.NoPen)
                continue
            is_big_pupil = self.state in (CharacterState.NOTICING, CharacterState.CONCERNED)
            pupil_r = self._pupil_size * (1.1 if is_big_pupil else 1.0)
            pupil = QPainterPath()
            pupil.addEllipse(QRectF(ex - pupil_r + self._look_x * 0.3, ey - pupil_r + self._look_y * 0.3, pupil_r * 2, pupil_r * 2))
            p.fillPath(pupil, QColor("#3d1f52"))
            hl_r = 2.5
            hl = QPainterPath()
            hl.addEllipse(QRectF(ex - 1 + self._look_x * 0.3, ey - 4 + self._look_y * 0.3, hl_r * 2, hl_r * 2))
            p.fillPath(hl, QColor(255, 255, 255, 220))
            if self.state == CharacterState.EXCITED:
                self._draw_sparkle(p, ex + 9, ey - 8, 4)
                if int(self._sparkle_phase * 2) % 3 == 0:
                    self._draw_sparkle(p, ex + 12, ey + 2, 3)

    def _draw_blush(self, p, ex, ey):
        if self._blush_alpha > 0.01:
            for side in (-1, 1):
                blush = QPainterPath()
                blush.addEllipse(QRectF(ex + side * 12 - 5, ey + 3, 10, 5))
                c = QColor(255, 180, 200, int(self._blush_alpha * 120))
                p.fillPath(blush, c)

    def _draw_sparkle(self, p, x, y, size):
        if self._cached_star_path is None:
            star = QPainterPath()
            for i in range(5):
                angle = i * 2 * pi / 5 - pi / 2
                outer_x = cos(angle) * size
                outer_y = sin(angle) * size
                if i == 0:
                    star.moveTo(outer_x, outer_y)
                else:
                    star.lineTo(outer_x, outer_y)
                inner_angle = angle + pi / 5
                inner_x = cos(inner_angle) * size * 0.4
                inner_y = sin(inner_angle) * size * 0.4
                star.lineTo(inner_x, inner_y)
            star.closeSubpath()
            self._cached_star_path = star
        p.save()
        p.translate(x, y)
        p.fillPath(self._cached_star_path, QColor(255, 230, 100, 200))
        p.restore()

    def _draw_mouth(self, p):
        mouth = QPainterPath()
        if self.state == CharacterState.PLEASED:
            mouth.moveTo(-6, 6)
            mouth.quadTo(0, 18, 6, 6)
            p.setPen(QPen(QColor("#5c3d70"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.EXCITED:
            mouth.moveTo(-8, 5)
            mouth.quadTo(0, 20, 8, 5)
            p.setPen(QPen(QColor("#5c3d70"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.LAUGHING:
            mouth.moveTo(-8, 6)
            mouth.quadTo(0, 22, 8, 6)
            p.setPen(QPen(QColor("#5c3d70"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.CONCERNED:
            mouth.moveTo(-6, 7)
            mouth.quadTo(0, 0, 6, 7)
            p.setPen(QPen(QColor("#7a5c8a"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.THINKING:
            mouth.moveTo(-4, 8)
            mouth.quadTo(0, 12, 5, 6)
            p.setPen(QPen(QColor("#5c3d70"), 2.0, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.SURPRISED:
            mouth.addEllipse(QRectF(-4, 6, 8, 8))
            p.fillPath(mouth, QColor("#4a2d5c"))
        elif self.state == CharacterState.PROUD:
            mouth.moveTo(-7, 6)
            mouth.quadTo(0, 16, 7, 6)
            p.setPen(QPen(QColor("#5c3d70"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.LISTENING:
            mouth.moveTo(-4, 8)
            mouth.quadTo(0, 11, 4, 8)
            p.setPen(QPen(QColor("#5c3d70"), 2.0, cap=Qt.RoundCap))
            p.drawPath(mouth)
        elif self.state == CharacterState.NOTICING:
            mouth.addEllipse(QRectF(-3, 4, 6, 6))
            p.fillPath(mouth, QColor("#5c3d70"))
        elif self.state == CharacterState.SLEEPY:
            pass
        elif self.state == CharacterState.PRESENTING:
            mouth.moveTo(-6, 6)
            mouth.quadTo(0, 12, 6, 6)
            p.setPen(QPen(QColor("#4a2d5c"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        else:
            mouth.moveTo(-5, 7)
            mouth.quadTo(0, 12, 5, 7)
            p.setPen(QPen(QColor("#5c3d70"), 2.5, cap=Qt.RoundCap))
            p.drawPath(mouth)
        p.setPen(Qt.NoPen)

    def _draw_caption(self, p, cx, by):
        if not self._caption or self._caption_alpha <= 0:
            return
        alpha = int(self._caption_alpha * 255)
        lines = []
        text = self._caption
        while len(text) > 32:
            split = text[:30].rfind(" ")
            if split < 10:
                split = 30
            lines.append(text[:split])
            text = text[split:].strip()
        if text:
            lines.append(text)
        bubble_w = max(100, min(220, max(len(l) * 7 for l in lines) + 24))
        line_h = 20
        bubble_h = len(lines) * line_h + 24
        bx = cx - bubble_w / 2
        by2 = by - 100 - bubble_h
        bubble = QPainterPath()
        br = 12
        bubble.moveTo(bx + br, by2)
        bubble.quadTo(bx, by2, bx, by2 + br)
        bubble.lineTo(bx, by2 + bubble_h - br)
        bubble.quadTo(bx, by2 + bubble_h, bx + br, by2 + bubble_h)
        bubble.lineTo(bx + bubble_w - br, by2 + bubble_h)
        bubble.quadTo(bx + bubble_w, by2 + bubble_h, bx + bubble_w, by2 + bubble_h - br)
        bubble.lineTo(bx + bubble_w, by2 + br)
        bubble.quadTo(bx + bubble_w, by2, bx + bubble_w - br, by2)
        bubble.closeSubpath()
        p.setPen(QPen(QColor(0, 0, 0, int(alpha * 0.15)), 1))
        p.fillPath(bubble, QColor(255, 255, 255, alpha))
        p.setPen(Qt.NoPen)
        f = p.font()
        f.setPointSize(10)
        f.setBold(False)
        p.setFont(f)
        p.setPen(QColor(30, 30, 40, alpha))
        for i, l in enumerate(lines):
            p.drawText(QRectF(bx + 14, by2 + 12 + i * line_h, bubble_w - 28, line_h), 0x84 | 0x02, l)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)
