import sys, os, textwrap
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate

from .constants import messages


class Render:
    def __init__(self):
        self.path = os.getcwd()

    def make_graph(self, data, icon):
        x = [0, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7]
        y = [data[0]] + data + [data[len(data) - 1]]

        f = interpolate.PchipInterpolator(x, y)
        x_new = np.arange(0, len(y) - 2, 0.01)
        y_new = f(x_new)

        fig = plt.figure(frameon=False)
        fig.set_size_inches(12, 4)
        ax = plt.subplot(111)
        ax.fill_between(x_new, y_new, min(y) - 1)
        ax.set_axis_off()

        buf = BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)

        plot = Image.open(buf)
        plot.load()
        buf.close()
        plot = self.png_crop(plot)

        grad = Image.open(f'{self.path}/resources/{icon}_grad.png').convert('RGBA')
        back = Image.new('RGBA', grad.size, (255, 255, 255, 0))

        plot = plot.resize(grad.size, resample=Image.ANTIALIAS)

        back.paste(grad, plot)
        return back

    def png_crop(self, image):
        """ Crops all transparent borders in png image """
        image_size = image.size
        image_box = image.getbbox()

        image_components = image.split()

        rgb_image = Image.new('RGB', image_size, (0, 0, 0))
        rgb_image.paste(image, mask=image_components[3])
        cropped_box = rgb_image.getbbox()

        if image_box != cropped_box:
            cropped = image.crop(cropped_box)
        return cropped

    def make_hourly(self, data, lang):
        city = data['city']
        temp = str(round(data['temperature'])) + '°'
        temp_chart = [data['temperature'], data['+2'], data['+4'], data['+6'], data['+8'], data['+10'], data['+12']]
        weather = data['summary'].lower()
        wind = str(round(data['wind'])) + messages['ms'][lang]
        humidity = str(int(data['humidity'] * 100)) + '%'
        feels_like = messages['feels_like'][lang] + str(round(data['apparentTemperature'])) + '°'
        bw_divs = [79, 186, 293, 400, 507, 614, 721]

        im = Image.new('RGBA', (800, 656), (255, 255, 255, 0))
        bg = Image.open(self.path + '/backgrounds/' + data['icon']
                        + '.png').convert("RGBA")
        card = Image.open(self.path + '/resources/card.png')
        ic = Image.open(self.path + '/icons/' + data['icon'] + '.png')
        ic.thumbnail((999, 180), resample=Image.ANTIALIAS)
        wind_ic = Image.open(self.path + '/icons/wind_ic.png')
        hum_ic = Image.open(self.path + '/icons/hum_ic.png')
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        graph = self.make_graph(temp_chart, data['icon'])

        font_h = self.path + '/fonts/ObjectSans-Heavy.otf'
        font_l = self.path + '/fonts/ObjectSans-Regular.otf'

        temp_font = ImageFont.truetype(font=font_h, size=108)
        temp_chart_font_now = ImageFont.truetype(font=font_h, size=25)
        temp_chart_font = ImageFont.truetype(font=font_l, size=25)
        city_font = ImageFont.truetype(font=font_l, size=32)
        feels_like_font = ImageFont.truetype(font=font_l, size=30)
        weather_font = ImageFont.truetype(font=font_h, size=43)
        weather_font_big = ImageFont.truetype(font=font_h, size=58)
        wind_font = ImageFont.truetype(font=font_l, size=29)
        time_font = ImageFont.truetype(font=font_l, size=24)
        time_font_now = ImageFont.truetype(font=font_h, size=24)

        im.paste(bg)
        im.paste(ic, (64, 36), ic)
        im.paste(card, (0, im.height - card.height), card)
        im.paste(graph, (24, im.height - graph.height - 20), graph)
        draw = ImageDraw.Draw(txt)
        text_size = ImageDraw.Draw(txt).textsize

        draw.text((im.width - text_size(city, city_font)[0] - 77, 47), city, font=city_font)
        draw.text((im.width - text_size(temp, temp_font)[0] - 77, 102), text=temp, font=temp_font)
        draw.text((im.width - text_size(feels_like, feels_like_font)[0] - 77, 197), text=feels_like,
                  font=feels_like_font, fill=(255, 255, 255, 221))
        draw.text(((im.width - text_size(wind, wind_font)[0] - 77), 283), text=wind, font=wind_font,
                  fill=(255, 255, 255, 221))
        draw.text(((im.width - text_size(humidity, wind_font)[0] - 77), 244), text=humidity, font=wind_font,
                  fill=(255, 255, 255, 221))
        im.paste(wind_ic, (im.width - text_size(wind, wind_font)[0] - 77 - 10 - wind_ic.width, 282), wind_ic)
        im.paste(hum_ic, (im.width - text_size(humidity, wind_font)[0] - 77 - 10 - hum_ic.width, 240), hum_ic)

        for x in bw_divs:
            for y in range(430, im.height - 1):
                yl, yc, yr = 0, 0, 0

                if im.getpixel((x, y)) == (255, 255, 255, 255):
                    continue
                else:
                    yc = y

                    for yy in range(430, im.height - 1):
                        if im.getpixel((x - 15, yy)) != (255, 255, 255, 255):
                            yl = yy
                            break
                        else:
                            continue

                    for yy in range(430, im.height - 1):
                        if im.getpixel((x + 15, yy)) != (255, 255, 255, 255):
                            yr = yy
                            break
                        else:
                            continue

                    if bw_divs.index(x) == 0:
                        draw.text(((x + 10 - text_size(str(temp_chart[bw_divs.index(x)]),
                                                       temp_chart_font_now)[0] / 2), min(yl, yc, yr) - 38),
                                  text=str(round(temp_chart[bw_divs.index(x)])) + '°',
                                  font=temp_chart_font_now, fill=(64, 64, 64, 255))
                    else:
                        draw.text(((x + 10 - text_size(str(temp_chart[bw_divs.index(x)]),
                                                       temp_chart_font)[0] / 2), min(yl, yc, yr) - 38),
                                  text=str(round(temp_chart[bw_divs.index(x)])) + '°',
                                  font=temp_chart_font, fill=(64, 64, 64, 221))
                    break

        time = data['time'].split(':')
        time_list = list()
        time_list.append(data['time'])
        hours = time[0]
        minutes = time[1]

        if int(hours) + 3 > 23:
            if int(hours) == 22:
                if int(minutes) > 30:
                    hours = '01'
                    time[1] = '00'
                    time_list.append('01:00')
                else:
                    hours = '00'
                    time[1] = '00'
                    time_list.append('00:00')

            elif int(hours) == 23:
                if int(minutes) > 30:
                    hours = '02'
                    time[1] = '00'
                    time_list.append('02:00')
                else:
                    hours = '01'
                    time[1] = '00'
                    time_list.append('01:00')

            else:
                if int(minutes) > 30:
                    hours = '00'
                    time[1] = '00'
                    time_list.append('00:00')
                else:
                    hours = '23'
                    time[1] = '00'
                    time_list.append('23:00')

        else:
            if int(minutes) > 30:
                hours = str(int(hours) + 3)
                time[0] = hours
                time[1] = '00'
                time_list.append(':'.join(time))
            else:
                hours = str(int(hours) + 2)
                time[0] = hours
                time[1] = '00'
                time_list.append(':'.join(time))

        for i in range(0, 5):
            if int(hours) + 2 > 23:
                if int(hours) % 2 == 0:
                    hours = '00'
                else:
                    hours = '01'
            else:
                hours = str(int(hours) + 2)
            time_plus = [hours, '00']
            time_list.append(':'.join(time_plus))

        for i in range(0, 7):
            if i:
                draw.text((bw_divs[i] - text_size(time_list[i])[0], 370), text=time_list[i], font=time_font,
                          fill=(48, 48, 48, 163))
            else:
                draw.text((bw_divs[i] - text_size(time_list[i])[0], 370), text=time_list[i], font=time_font_now,
                          fill=(64, 64, 64, 255))

        lines = textwrap.wrap(weather, width=17)
        if len(weather) < 13:
            draw.text((64, 253), text=lines[0], font=weather_font_big)
        else:
            if len(lines) > 2:
                liness = textwrap.wrap(weather, width=23)
                draw.text((64, 230), text=liness[0], font=ImageFont.truetype(font=font_h, size=32))
                try:
                    draw.text((64, text_size(liness[0], weather_font)[1] + 230 + 3), text=liness[1],
                              font=ImageFont.truetype(font=font_h, size=32))
                except:
                    pass
                try:
                    draw.text((64, text_size(liness[0], weather_font)[1] * 2 + 230 + 3), text=liness[2],
                              font=ImageFont.truetype(font=font_h, size=32))
                except:
                    pass
            elif len(lines) > 1:
                draw.text((64, 245), text=lines[0], font=weather_font)
                draw.text((64, text_size(lines[0], weather_font)[1] + 245 + 5), text=lines[1], font=weather_font)
            else:
                draw.text((64, 253), text=lines[0], font=weather_font)

        im = Image.alpha_composite(im, txt)
        im.show()

        bio = BytesIO()
        bio.name = 'image.png'
        im.save(bio, 'png')
        bio.seek(0)

        return bio
