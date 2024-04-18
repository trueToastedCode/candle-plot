class CandlestickPlot:
    def __init__(
        self,
        df,
        i,
        width = 2000,  # image width, height
        height = 1000,  # image height
        candle_body_width = 11 / 1,  # n pixel per m time unit(s)
        candle_body_padding = 2,  # vertical padding for the body
        candle_shadow_width = 1,  # n pixel
        candle_height_factor = 0.5 / 1e-4,  # n pixel per m of price unit
        ref_x = None,  # horizontal starting point
        ref_y = None,  # vertical starting point
        background = (23, 27, 33),
        candle_body_bullish_color = (46, 204, 113),
        candle_shadow_bullish_color = (32, 142, 79),
        candle_body_bearish_color = (231, 76, 60),
        candle_shadow_bearish_color = (181, 37, 22)
    ):
        self.df = df
        self.i = i
        self.width = width
        self.height = height
        self.candle_body_width = candle_body_width
        self.candle_body_padding = candle_body_padding
        self.candle_shadow_width = candle_shadow_width
        self.candle_height_factor = candle_height_factor
        self.ref_x = width - candle_body_width if ref_x is None else ref_x
        self.ref_y = height * 0.5 if ref_y is None else ref_y
        self.background = background
        self.candle_body_bullish_color = candle_body_bullish_color
        self.candle_shadow_bullish_color = candle_shadow_bullish_color
        self.candle_body_bearish_color = candle_body_bearish_color
        self.candle_shadow_bearish_color = candle_shadow_bearish_color
        
        # calculate the horizontal offset of the shadow to be added to the left coordinate
        self.candle_shadow_offset = (candle_body_width - candle_shadow_width) * 0.5
        
        # calculate the maximum amount of candles in one image
        self.max_candle_count = math.ceil(self.ref_x / candle_body_width) + 1
        
        # calculate the amount of candles that need to be rendered
        self.candle_count = self.i + 1 \
            if self.i - self.max_candle_count + 1 < 0 \
            else self.max_candle_count
        
        # calculate ref price so that the figure will be vertically centered
        _df = self.df[self.i - self.candle_count + 1 : i + 1]
        plot_low = _df.Low.min()
        plot_high = _df.High.max()
        self.ref_price = plot_low + (plot_high - plot_low) * 0.5
        
        self.render_queue = [(0, self._plot_candlesticks)]

    def calc_top_from_price(self, price):
        return self.ref_y - (price - self.ref_price) * self.candle_height_factor

    def calc_left_from_idx(self, idx, candle_center=True):
        offset = self.candle_body_width * (0.5 if candle_center else 0)
        return self.ref_x + (idx - self.i) * self.candle_body_width + offset

    def add_line(self, start, end, color='yellow', width=3, layer=2):
        self.render_queue.append(
            (
                layer,
                lambda image, draw: self._plot_line(
                    image,
                    draw,
                    (self.calc_left_from_idx(start[0]), self.calc_top_from_price(start[1])),
                    (self.calc_left_from_idx(end[0]), self.calc_top_from_price(end[1])),
                    color,
                    width
                )
            )
        )

    def add_point(self, pos, offset=(0, 0), color='aqua', size=9, layer=1):
        self.render_queue.append(
            (
                layer,
                lambda image, draw: self._plot_point(
                    image,
                    draw,
                    (self.calc_left_from_idx(pos[0]), self.calc_top_from_price(pos[1])),
                    offset,
                    color,
                    size
                )
            )
        )

    def _plot_candlesticks(self, image, draw):
        # render each candle
        for j in range(self.candle_count):
            # calculate the current offset that needs to be added to i,
            # in order to get the current index in df
            i_offset = -self.candle_count + j + 1
            
            # calculate the current index in df
            idx = self.i + i_offset

            # calculate the left and right coordinate of the candle
            left = self.calc_left_from_idx(self.i + i_offset, False)
            right = left + self.candle_body_width

            # sort open and close into lower and higher price
            body_low_pirce, body_high_price = sorted((self.df.Open[idx], self.df.Close[idx]))

            # choose candle color
            color_body, color_shadow = (self.candle_body_bullish_color, self.candle_shadow_bullish_color) \
                if self.df.Open[idx] < self.df.Close[idx] \
                else (self.candle_body_bearish_color, self.candle_shadow_bearish_color)

            # draw shadow
            draw.rectangle(
                (
                    left + self.candle_shadow_offset,
                    self.calc_top_from_price(self.df.High[idx]),
                    right - self.candle_shadow_offset,
                    self.calc_top_from_price(self.df.Low[idx])
                ),
                fill=color_shadow
            )
        
            # draw body
            draw.rectangle(
                (
                    left + self.candle_body_padding,
                    self.calc_top_from_price(body_high_price),
                    right - self.candle_body_padding,
                    self.calc_top_from_price(body_low_pirce)
                ),
                fill=color_body
            )

    def _plot_line(self, image, draw, start, end, color, width):
        draw.line((start, end), fill=color, width=width)

    def _plot_point(self, image, draw, pos, offset, color, size):
        radius = size * 0.5
        pos = pos[0] + offset[0], pos[1] + offset[1]
        draw.ellipse(
            (
                (pos[0] - radius, pos[1] - radius),
                (pos[0] + radius, pos[1] + radius),
            ),
            fill=color
        )
    
    def plot(self):
        image = Image.new("RGB", (self.width, self.height), self.background)
        
        draw = ImageDraw.Draw(image)

        self.render_queue = sorted(self.render_queue, key=lambda x: x[0])
        
        for _, f in self.render_queue:
            f(image, draw)

        return image
