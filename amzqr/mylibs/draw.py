# -*- coding: utf-8 -*-

import os

from PIL import Image

from amzqr.mylibs.constant import PIXELS_PER_MODULE


def hex_to_rgba(hex_str, alpha=255):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = "".join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)

def draw_qrcode(abspath, qrmatrix, rounded=False, logo=None, transparent=False, fg_color="#000000", box_size=None):
    from PIL import ImageDraw, ImageChops

    if box_size == PIXELS_PER_MODULE:
        unit_len = PIXELS_PER_MODULE
        x = y = 4 * unit_len
        pic = Image.new("1", [(len(qrmatrix) + 8) * unit_len] * 2, "white")

        for line in qrmatrix:
            for module in line:
                if module:
                    draw_a_black_unit(pic, x, y, unit_len)
                x += unit_len
            x, y = 4 * unit_len, y + unit_len

        saving = os.path.join(abspath, "qrcode.png")
        pic.save(saving)
        return saving

    if box_size is None:
        box_size = 20

    N = len(qrmatrix)
    quiet_zone = 4
    img_size = (N + 2 * quiet_zone) * box_size

    fill_color = hex_to_rgba(fg_color, 255)
    # If transparent, main background and cutout are completely transparent
    main_bg_color = (255, 255, 255, 0) if transparent else (255, 255, 255, 255)
    # The card behind the logo must ALWAYS be solid white for readability, unless transparent
    logo_bg_color = (255, 255, 255, 255)

    pic = Image.new("RGBA", (img_size, img_size), main_bg_color)
    draw = ImageDraw.Draw(pic)

    def is_finder(r, c):
        if 0 <= r <= 6 and 0 <= c <= 6:
            return True
        if 0 <= r <= 6 and N - 7 <= c <= N - 1:
            return True
        if N - 7 <= r <= N - 1 and 0 <= c <= 6:
            return True
        return False

    if rounded:
        # 0.25 makes it a rounded square (borda arredondada) instead of a circle (bolinha)
        mod_radius = int(box_size * 0.25)
        for r in range(N):
            for c in range(N):
                if qrmatrix[r][c] and not is_finder(r, c):
                    # -1 and +1 expand the modules slightly to overlap and remove white anti-aliasing seams (riscos)
                    x0 = (quiet_zone + c) * box_size - 1
                    y0 = (quiet_zone + r) * box_size - 1
                    x1 = (quiet_zone + c + 1) * box_size + 1
                    y1 = (quiet_zone + r + 1) * box_size + 1
                    draw.rounded_rectangle([x0, y0, x1, y1], radius=mod_radius, fill=fill_color)

        finder_corners = [(0, 0), (0, N - 7), (N - 7, 0)]
        for (r_off, c_off) in finder_corners:
            fx0 = (quiet_zone + c_off) * box_size
            fy0 = (quiet_zone + r_off) * box_size
            fx1 = fx0 + 7 * box_size
            fy1 = fy0 + 7 * box_size

            # Use outline to avoid filling the inner cutout, so transparent background shows through
            draw.rounded_rectangle([fx0, fy0, fx1, fy1], radius=int(box_size * 1.8), outline=fill_color, width=box_size)
            draw.rounded_rectangle([fx0 + 2 * box_size, fy0 + 2 * box_size, fx1 - 2 * box_size, fy1 - 2 * box_size], radius=int(box_size * 0.8), fill=fill_color)
    else:
        for r in range(N):
            for c in range(N):
                if qrmatrix[r][c]:
                    x0 = (quiet_zone + c) * box_size
                    y0 = (quiet_zone + r) * box_size
                    x1 = x0 + box_size
                    y1 = y0 + box_size
                    draw.rectangle([x0, y0, x1, y1], fill=fill_color)

    if logo and os.path.isfile(logo):
        try:
            logo_img = Image.open(logo).convert("RGBA")
            
            # Automatically remove solid black outer backgrounds if image has no native transparency
            w, h = logo_img.size
            if w > 2 and h > 2:
                corners = [
                    logo_img.getpixel((0, 0)),
                    logo_img.getpixel((w - 1, 0)),
                    logo_img.getpixel((0, h - 1)),
                    logo_img.getpixel((w - 1, h - 1))
                ]
                if all(c[0] < 18 and c[1] < 18 and c[2] < 18 and c[3] == 255 for c in corners):
                    gray = logo_img.convert("RGB").convert("L")
                    alpha_mask = gray.point(lambda p: 255 if p > 15 else 0)
                    logo_img.putalpha(alpha_mask)

            logo_target_size = int(img_size * 0.20)
            logo_img.thumbnail((logo_target_size, logo_target_size), Image.Resampling.LANCZOS)
            
            lw, lh = logo_img.size
            center_x, center_y = img_size // 2, img_size // 2

            bg_radius = max(lw, lh) // 2 + int(box_size * 0.8)
            
            if transparent:
                # Punch a hole in the alpha channel
                mask = Image.new("L", pic.size, 255)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([center_x - bg_radius, center_y - bg_radius, center_x + bg_radius, center_y + bg_radius], fill=0)
                
                _, _, _, a = pic.split()
                new_a = ImageChops.multiply(a, mask)
                pic.putalpha(new_a)
            else:
                draw.ellipse([center_x - bg_radius, center_y - bg_radius, center_x + bg_radius, center_y + bg_radius], fill=logo_bg_color)

            logo_x = center_x - lw // 2
            logo_y = center_y - lh // 2
            pic.paste(logo_img, (logo_x, logo_y), logo_img)
        except Exception:
            pass

    saving = os.path.join(abspath, "qrcode.png")
    # Save as RGBA to preserve transparency
    pic.save(saving)
    return saving


def draw_a_black_unit(p, x, y, ul):
    for i in range(ul):
        for j in range(ul):
            p.putpixel((x + i, y + j), 0)
