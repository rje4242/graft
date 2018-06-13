import math

import attr

from graftlib.dot import Dot
from graftlib.line import Line
from graftlib.pt import Pt


@attr.s
class Functions:
    state = attr.ib()
    rand = attr.ib()
    fork_callback = attr.ib()

    def step(self, env):
        th = self.state.theta()
        s = self.state.step()
        old_pos = self.state.pos()
        new_pos = Pt(
            old_pos.x + s * math.sin(th),
            old_pos.y + s * math.cos(th),
        )
        self.state.set_pos(new_pos)
        return [Line(
            old_pos,
            new_pos,
            color=self.state.color(),
            size=self.state.brush_size()
        )]

    def dot(self, env):
        return [Dot(
            self.state.pos(),
            self.state.color(),
            self.state.brush_size()
        )]

    def line_to(self, env):
        return [Line(
            self.state.prev_pos(),
            self.state.pos(),
            color=self.state.color(),
            size=self.state.brush_size(),
        )]

    def jump(self, env):
        self.step(env)
        return [None]

    def random(self, env):
        return [float(self.rand.__call__(-10, 10))]

    def fork(self, env):
        return [self.fork_callback.__call__()]
