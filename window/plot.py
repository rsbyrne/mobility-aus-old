import numpy as np
import math

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import get_cmap

# from everest.disk import tempname
from ._fig import Fig as _Fig
from . import analysis
from .data import Data

def draw(variety, *args, size = (3, 3), **kwargs):
    fig = Canvas(size = size)
    ax = fig.make_ax()
    getattr(ax, variety)(*args, **kwargs)
    return fig.fig
def scatter(*args, **kwargs):
    return draw('scatter', *args, **kwargs)
def line(*args, **kwargs):
    return draw('line', *args, **kwargs)

def ifnone(x, y):
    return y if x is None else x

class Canvas(_Fig):

    def __init__(self,
            name = None,
            shape = (1, 1),
            size = (3, 3), # inches
            dpi = 100, # pixels per inch
            facecolour = 'white',
            edgecolour = 'black',
            **kwargs
            ):

        fig = Figure(
            figsize = size,
            dpi = dpi,
            facecolor = facecolour,
            edgecolor = edgecolour,
            **kwargs
            )

        nrows, ncols = shape

        self.shape = shape
        self.nrows, self.ncols = nrows, ncols
        self.size = size

        self._updateFns = []
        self.fig = fig

        self.clear()

        self.ax = self.make_ax

        super().__init__()

    def make_ax(self, place = (0, 0), superimpose = False, **kwargs):
        rowNo, colNo = place
        index = self._calc_index(place)
        axObj = Ax(self, index = index, **kwargs)
        self.axes[rowNo][colNo].append(axObj)
        return axObj

    def clear(self):
        self.fig.clf()
        self.axes = [
            [[] for col in range(self.ncols)] \
                for row in range(self.nrows)
            ]

    def _calc_index(self, place):
        rowNo, colNo = place
        if colNo >= self.shape[1] or rowNo >= self.shape[0]:
            raise ValueError("Prescribed row and col do not exist.")
        return (self.ncols * rowNo + colNo)

    def _update(self):
        for fn in self._updateFns:
            fn()

    def _save(self, filepath):
        self.fig.savefig(filepath)

    def _show(self):
        FigureCanvas(self.fig)
        return self.fig

class Ax:

    _plotFuncs = {
        'line': 'plot',
        'scatter': 'scatter'
        }

    def __init__(self,
            canvas = None,
            index = 0,
            projection = 'rectilinear',
            name = None,
            **kwargs
            ):

        if canvas is None:
            canvas = Canvas()

        if name is None:
            name = tempname()

        ax = canvas.fig.add_subplot(
            canvas.nrows,
            canvas.ncols,
            index + 1,
            projection = projection,
            label = name,
            **kwargs
            )

        self.canvas, self.index, self.projection, self.name = \
            canvas, index, projection, name

        colNo = index % canvas.ncols
        rowNo = int((index - colNo) / canvas.ncols)
        self.colNo, self.rowNo = colNo, rowNo

        self.ax = ax
        self.datas = []
        self.title = ''

        self.set_margins()

        self.axisYVisible = True
        self.axisXVisible = True
        self.axisYSide = 'left'
        self.axisXSide = 'bottom'

        self.gridXMajorAlpha = 0.5
        self.gridXMinorAlpha = 0.25
        self.gridYMajorAlpha = 0.5
        self.gridYMinorAlpha = 0.25
        self.gridXMajorVisible = True
        self.gridXMinorVisible = True
        self.gridYMajorVisible = True
        self.gridYMinorVisible = True

        self.facecolour = None
        self.facecolourVisible = True
        axStack = self._get_axStack()
        self.facecolour = axStack[0].facecolour
        self.facecolourVisible = axStack[0].facecolourVisible
        self.set_facecolour()

    def _get_axStack(self):
        axStack = self.canvas.axes[self.rowNo][self.colNo]
        if len(axStack):
            return axStack
        else:
            return [self,]

    def _autoconfigure_axis(self,
            i,
            data,
            scale = 'linear',
            ticksPerInch = 1,
            alpha = 0.5,
            hide = False
            ):
        localSize = self.canvas.size[i] / self.canvas.shape[::-1][i]
        nTicks = ticksPerInch * localSize
        label, tickVals, minorTickVals, ticklabels, lims = \
            data.auto_axis_configs(nTicks)
        tupFn = lambda val: (val, None) if i == 0 else (None, val)
        self.set_scales(*tupFn(scale))
        self.set_lims(*tupFn(lims))
        self.set_ticks_major(*tupFn((tickVals, ticklabels)))
        self.set_ticks_minor(*tupFn(minorTickVals))
        self.set_label(*tupFn(label))
        self.set_grid_i_major(i, alpha)
        self.set_grid_i_minor(i, alpha / 2.)
        if hide:
            self.toggle_axis_i(i)

    def _autoconfigure_axis_x(self, *args, **kwargs):
        self._autoconfigure_axis(0, *args, **kwargs)
    def _autoconfigure_axis_y(self, *args, **kwargs):
        self._autoconfigure_axis(1, *args, **kwargs)

    # def hide_axis_i(self):
    #     if i == 0:
    #         self.hide_axis_x()
    #     elif i == 1:
    #         self.hide_axis_y()
    #     else:
    #         raise KeyError
    # def hide_axis_x(self):
    #     self.ax.xaxis.label.set_visible(False)
    #     # for tic in self.ax.xaxis.get_major_ticks():
    #     #     tic.set_visible(False)
    #     # for tic in self.ax.xaxis.get_minor_ticks():
    #     #     tic.set_visible(False)
    # def hide_axis_y(self):
    #     self.ax.yaxis.label.set_visible(False)
    #     # for tic in self.ax.yaxis.get_major_ticks():
    #     #     tic.set_visible(False)
    #     # for tic in self.ax.yaxis.get_minor_ticks():
    #     #     tic.set_visible(False)

    def toggle_axis_i(self):
        if i == 0:
            self.toggle_axis_x()
        elif i == 1:
            self.toggle_axis_y()
        else:
            raise KeyError
    def toggle_axes(self):
        self.toggle_axis_x()
        self.toggle_axis_y()
    def toggle_axis_x(self):
        self.axisXVisible = not self.axisXVisible
        self.ax.xaxis.label.set_visible(self.axisXVisible)
        for tic in self.ax.xaxis.get_major_ticks():
            tic.set_visible(self.axisXVisible)
        for tic in self.ax.xaxis.get_minor_ticks():
            tic.set_visible(self.axisXVisible)
    def toggle_axis_y(self):
        self.axisYVisible = not self.axisYVisible
        self.ax.yaxis.label.set_visible(self.axisYVisible)
        for tic in self.ax.yaxis.get_major_ticks():
            tic.set_visible(self.axisYVisible)
        for tic in self.ax.yaxis.get_minor_ticks():
            tic.set_visible(self.axisYVisible)

    def swap_sides_axis_i(self):
        if i == 0:
            self.swap_sides_axis_x()
        elif i == 1:
            self.swap_sides_axis_y()
        else:
            raise KeyError
    def swap_sides_axes(self):
        self.swap_sides_axis_x()
        self.swap_sides_axis_y()
    def swap_sides_axis_x(self):
        if self.axisXSide == 'bottom':
            self.axisXSide = 'top'
            self.ax.xaxis.tick_top()
        elif self.axisXSide == 'top':
            self.axisXSide = 'bottom'
            self.ax.xaxis.tick_bottom()
        else:
            raise Exception
        self.ax.xaxis.set_label_position(self.axisXSide)
    def swap_sides_axis_y(self):
        if self.axisYSide == 'left':
            self.axisYSide = 'right'
            self.ax.yaxis.tick_right()
        elif self.axisYSide == 'right':
            self.axisYSide = 'left'
            self.ax.yaxis.tick_left()
        else:
            raise ValueError
        self.ax.yaxis.set_label_position(self.axisYSide)

    def clear(self):
        self.ax.clear()
        self.datas = []

    def set_scales(self, x = 'linear', y = 'linear'):
        if not x is None: self.ax.set_xscale(x)
        if not y is None: self.ax.set_yscale(y)

    def set_lims(self, x = None, y = None):
        if not x is None: self.ax.set_xlim(x)
        if not y is None: self.ax.set_ylim(y)

    def set_ticks_major(self, x = None, y = None):
        self.set_ticks(x = x, y = y, minor = False)
    def set_ticks_minor(self, x = None, y = None):
        self.set_ticks(x = x, y = y, minor = True)
    def set_ticks(self, x = None, y = None, minor = False):
        if not x is None:
            if type(x) is tuple:
                xticks, xticklabels = x
            else:
                xticks, xticklabels = x, None
            if not xticks is None:
                self.ax.set_xticks(
                    xticks,
                    minor = minor
                    )
            if not xticklabels is None:
                self.ax.set_xticklabels(
                    xticklabels,
                    rotation = 45,
                    minor = minor
                    )
        if not y is None:
            if type(y) is tuple:
                yticks, yticklabels = y
            else:
                yticks, yticklabels = y, None
            if not yticks is None:
                self.ax.set_yticks(
                    yticks,
                    minor = minor
                    )
            if not yticklabels is None:
                self.ax.set_yticklabels(
                    yticklabels,
                    minor = minor
                    )

    def set_margins(self, x = 0., y = 0.):
        self.ax.set_xmargin(x)
        self.ax.set_ymargin(y)

    def set_title(self, title = None):
        if not title is None:
            self.title = title
        self.ax.set_title(self.title)

    def set_grid_i_major(self, i, alpha = None):
        if i == 0:
            self.set_grid_x_major(alpha = alpha)
        elif i == 1:
            self.set_grid_y_major(alpha = alpha)
        else:
            raise KeyError
    def set_grid_i_minor(self, i, alpha = None):
        if i == 0:
            self.set_grid_x_minor(alpha = alpha)
        elif i == 1:
            self.set_grid_y_minor(alpha = alpha)
        else:
            raise KeyError
    def set_grid_x_major(self, alpha = None):
        if alpha is None:
            alpha = self.gridXMajorAlpha
        else:
            self.gridXMajorAlpha = alpha
        if not self.gridXMajorVisible:
            alpha = 0.
        self.ax.grid(axis = 'x', which = 'major', alpha = alpha)
    def set_grid_x_minor(self, alpha = None):
        if alpha is None:
            alpha = self.gridXMinorAlpha
        else:
            self.gridXMinorAlpha = alpha
        if not self.gridXMinorVisible:
            alpha = 0.
        self.ax.grid(axis = 'x', which = 'minor', alpha = alpha)
    def set_grid_y_major(self, alpha = None):
        if alpha is None:
            alpha = self.gridYMajorAlpha
        else:
            self.gridYMajorAlpha = alpha
        if not self.gridYMajorVisible:
            alpha = 0.
        self.ax.grid(axis = 'y', which = 'major', alpha = alpha)
    def set_grid_y_minor(self, alpha = None):
        if alpha is None:
            alpha = self.gridYMinorAlpha
        else:
            self.gridYMinorAlpha = alpha
        if not self.gridYMinorVisible:
            alpha = 0.
        self.ax.grid(axis = 'y', which = 'minor', alpha = alpha)
    def toggle_grid(self):
        self.toggle_grid_major()
        self.toggle_grid_minor()
    def toggle_grid_major(self):
        self.toggle_grid_x_major()
        self.toggle_grid_y_major()
    def toggle_grid_minor(self):
        self.toggle_grid_x_minor()
        self.toggle_grid_y_minor()
    def toggle_grid_x_major(self):
        self.gridXMajorVisible = not self.gridXMajorVisible
        self.set_grid_x_major()
    def toggle_grid_x_minor(self):
        self.gridXMinorVisible = not self.gridXMinorVisible
        self.set_grid_x_minor()
    def toggle_grid_y_major(self):
        self.gridYMajorVisible = not self.gridYMajorVisible
        self.set_grid_y_major()
    def toggle_grid_y_minor(self):
        self.gridYMinorVisible = not self.gridYMinorVisible
        self.set_grid_y_minor()

    def set_facecolour(self, colour = None):
        self.ax.set_facecolor((0, 0, 0, 0))
        if colour is None:
            colour = self.facecolour
        if not self.facecolourVisible:
            setcolour = (0, 0, 0, 0)
        elif colour is None:
            setcolour = (0, 0, 0, 0)
        else:
            setcolour = colour
        axStack = self._get_axStack()
        axStack[0].ax.set_facecolor(setcolour)
        for ax in axStack:
            ax.facecolour = colour
    def toggle_facecolour(self):
        self.set_facecolour()
        axStack = self._get_axStack()
        for ax in axStack:
            ax.facecolourVisible = not self.facecolourVisible

    def set_label(self, x = '', y = ''):
        if not x is None:
            self.ax.set_xlabel(x)
        if not y is None:
            self.ax.set_ylabel(y)

    def draw(self,
            x,
            y,
            c = None,
            s = None,
            l = None,
            multi = False,
            variety = 'scatter',
            title = None,
            clear = False,
            **kwargs
            ):
        if clear:
            self.clear()
        if multi:
            newDatas = []
            if c is None:
                c = [None] * len(x)
            if s is None:
                s = [None] * len(x)
            if l is None:
                l = [''] * len(x)
            for sx, sy, sc, ss, sl in zip(x, y, c, s, l):
                sx, sy, = Data(sx), Data(sy)
                newDatas.append((sx, sy, sc, ss, sl))
                self.datas.append((sx, sy, sc, ss, sl))
        else:
            x, y = Data(x), Data(y)
            self.datas.append((x, y, c, s, l))
        xDatas, yDatas, cs, ss, ls = list(zip(*self.datas))
        minxLim, minxCapped = sorted(
            [(d.lims[0], d.capped[0]) for d in xDatas],
            key = lambda d: d[0]
            )[0]
        maxxLim, maxxCapped = sorted(
            [(d.lims[1], d.capped[1]) for d in xDatas],
            key = lambda d: d[0]
            )[-1]
        minyLim, minyCapped = sorted(
            [(d.lims[0], d.capped[0]) for d in yDatas],
            key = lambda d: d[0]
            )[0]
        maxyLim, maxyCapped = sorted(
            [(d.lims[1], d.capped[1]) for d in yDatas],
            key = lambda d: d[0]
            )[-1]
        allX = Data(
            np.concatenate([d.data for d in xDatas]),
            lims = (minxLim, maxxLim),
            capped = (minxCapped, maxxCapped),
            label = ', '.join(frozenset([d.label for d in xDatas if len(d.label)]))
            )
        allY = Data(
            np.concatenate([d.data for d in yDatas]),
            lims = (minyLim, maxyLim),
            capped = (minyCapped, maxyCapped),
            label = ', '.join(frozenset([d.label for d in yDatas if len(d.label)]))
            )
        self._autoconfigure_axis_x(allX)
        self._autoconfigure_axis_y(allY)
        if multi:
            for x, y, c, s, l in newDatas:
                self._new_artist(x, y, c, s, l, variety)
        else:
            self._new_artist(x, y, c, s, l, variety)
        self.set_title(title)
    def _new_artist(self, x, y, c, s, l, variety = 'line', **kwargs):
        plotFunc = getattr(self.ax, self._plotFuncs[variety])
        plotKwargs = {**kwargs}
        # plotKwargs['x'] = x.data
        # plotKwargs['y'] = y.data
        if not c is None:
            plotKwargs['c'] = c
        if not s is None:
            plotKwargs['s'] = s
        if not l is None:
            plotKwargs['label'] = l
        plotFunc(x.data, y.data, **plotKwargs)
    def multidraw(self, *args, **kwargs):
        self.draw(*args, multi = True, **kwargs)
    def scatter(self, *args, **kwargs):
        self.draw(*args, variety = 'scatter', **kwargs)
    def multiscatter(self, *args, **kwargs):
        self.scatter(*args, multi = True, **kwargs)
    def line(self, *args, **kwargs):
        self.draw(*args, variety = 'line', **kwargs)
    def multiline(self, *args, **kwargs):
        self.line(*args, multi = True, **kwargs)

    def annotate(self,
            x,
            y,
            label,
            arrowProps = dict(arrowstyle = 'simple'),
            points = None,
            **kwargs
            ):
        if points is None:
            points = (10, 10)
        location = (x, y)
        labelLocation = ('offset points', 'offset points')
        self.ax.annotate(
            label,
            location,
            xytext = points,
            textcoords = ('offset points', 'offset points'),
            arrowprops = arrowProps,
            **kwargs
            )

    def show(self):
        return self.canvas.show()
