# calendrier.py
"""
System to create an image with the calendar
of the selected month providing all special
days for that specific month.

Author: elcoyote solitaire
"""
import calendar
import os
import ephem
import holidays
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dateutil.easter import easter
from PIL import Image, ImageDraw, ImageFont


def get_calendar_data(year: int, month: int):
    """
    Get the data/matrix for the calendar

    Args:
        year as int for the year
        month as int for the month (1~12)

    Returns:
         data as dict for the month's matrix
    """
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    return {
        "year": year,
        "month": month,
        "matrix": month_days
    }


def render_calendar_image(data, specials):
    """
    Generates a calendar from set of data

    Args:
        data as dict for the year, month, and matrix for the days
        specials as dict for the special events of the month
    """
    width = 1000
    height = 1000
    footer_start_y = 720
    cell_w = width // 7
    cell_h = 90
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        day_font = ImageFont.truetype("arial.ttf", 28)
        event_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = ImageFont.load_default()
        day_font = ImageFont.load_default()
        event_font = ImageFont.load_default()
    title = f"{calendar.month_name[data['month']]} {data['year']}"
    draw.text((width // 2, 30), title, fill="black", anchor="mm", font=title_font)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, day in enumerate(days):
        draw.text(
            (i * cell_w + cell_w // 2, 100),
            day,
            fill="black",
            anchor="mm",
            font=day_font
        )
    start_y = 140
    for row_idx, week in enumerate(data["matrix"]):
        for col_idx, day in enumerate(week):
            if day == 0:
                continue
            center_x = col_idx * cell_w + cell_w // 2
            center_y = start_y + row_idx * cell_h + cell_h // 2
            color = "red" if day in specials else "black"
            draw.text(
                (center_x, center_y),
                str(day),
                fill=color,
                font=day_font,
                anchor="mm"
            )
    draw.line((50, footer_start_y - 20, width - 50, footer_start_y - 20), fill="black", width=2)
    y_text = footer_start_y
    line_spacing = 32
    sorted_days = sorted(specials.keys())
    if sorted_days:
        for day in sorted_days:
            events = specials[day].split(" | ")
            for event in events:
                event_text = f"{day}: {event}"
                draw.text((50, y_text), event_text, fill="black", font=event_font)
                y_text += line_spacing
    else:
        draw.text((80, y_text), "No special events this month.",
                  fill="gray", font=event_font)
    filename = f"{data['year']}_{data['month']:02d}_calendar.png"
    filepath = os.path.join(os.getcwd(), filename)
    img.save(filepath, format="PNG")
    print(f"Calendar saved to: {filepath}")


def get_dst_transitions(year, month, tz_name):
    """
    Verify for daytime saving days (start/end)

    Args:
        year as int for the year
        month as int for the month (1~12)
        tz_name as str for the timezone ("America/Montreal" used)

    Returns:
        transitions as dict for daytime saving days
    """
    timez = ZoneInfo(tz_name)
    transitions = {}
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        day1 = datetime(year, month, day, 12, tzinfo=timez)
        day2 = day1 + timedelta(days=1)
        if day1.dst() != day2.dst():
            if day2.dst() > day1.dst():
                transitions[day + 1] = "Daylight Saving Time Starts"
            else:
                transitions[day + 1] = "Daylight Saving Time Ends"
    return transitions


def get_recurring_observances(month):
    """
    List of recurring days through the years

    Args:
        month as int for the month (1~12)

    Returns:
         events as dict for the static events of the year
    """
    events = {}
    fixed = [
        (2, 14, "Valentine's Day"),
        (3, 8, "International Women's Day"),
        (3, 17, "St. Patrick's Day"),
        (4, 22, "Earth Day"),
        (5, 1, "International Workers' Day"),
        (10, 31, "Halloween"),
        (11, 11, "Remembrance Day"),
        (12, 24, "Christmas Eve"),
        (12, 31, "New Year's Eve"),
    ]
    for monthz, day, name in fixed:
        if monthz == month:
            events[day] = name
    return events


def get_public_holidays(year, month, country, subdiv=None):
    """
    Generates a dictionary of holidays for the country

    The dictionary combines the country's holidays and the
    subdivision's holidays if any subdivision is specified

    Args:
        year as int for the year
        month as int for the month (1~12)
        country as str for the initial of the country (CA, USA, FR)
        subdiv as str for the state/province/sub area

    Returns:
        public as dict for the public holidays of the year/month
    """
    country_h = holidays.country_holidays(country, years=year, observed=True)
    subdiv_h = {}
    if subdiv:
        subdiv_h = holidays.country_holidays(
            country,
            subdiv=subdiv,
            years=year
        )
    merged = {}
    for day, name in country_h.items():
        if day.month == month:
            merged[day] = name
    for day, name in subdiv_h.items():
        if day.month == month:
            if day in merged:
                if name not in merged[day]:
                    merged[day] += f" | {name}"
            else:
                merged[day] = name
    return {day.day: name for day, name in merged.items()}


def get_easter_related(year, month):
    """
    Checks for Easter dates with the year/month

    Args:
        year as int for the year
        month as int for the month (1~12)

    Returns:
        events as dict for the Easter related day of the year/month
    """
    events = {}
    easter_sunday = easter(year)
    good_friday = easter_sunday - timedelta(days=2)
    easter_monday = easter_sunday + timedelta(days=1)
    candidates = [
        (good_friday, "Good Friday"),
        (easter_sunday, "Easter Sunday"),
        (easter_monday, "Easter Monday"),
    ]
    for day, name in candidates:
        if day.month == month:
            events[day.day] = name
    return events


def merge_event_dicts(*dicts):
    """
    Safely merge all dictionaries for the special dates

    Args:
        dicts as *arg for the name of the dictionaries to merge

    Returns:
         final as dict for the sorted, duplicateless special days of the year/month
    """
    merged = {}
    for dayz in dicts:
        for day, name in dayz.items():
            if day not in merged:
                merged[day] = set()
            merged[day].add(name)
    final = {}
    for day in sorted(merged):
        final[day] = " | ".join(sorted(merged[day]))
    return final


def get_astronomical_events(year, month):
    """
    Generates the days for the Equinoxes and Solstices of the year/month

    Args:
        year as int for the year
        month as int for the month (1~12)

    Returns:
        events as dict for the astral events of the year/month
    """
    events = {}
    spring = ephem.next_vernal_equinox(f"{year}/1/1")
    spring_date = ephem.Date(spring).datetime().date()
    summer = ephem.next_summer_solstice(f"{year}/1/1")
    summer_date = ephem.Date(summer).datetime().date()
    autumn = ephem.next_autumnal_equinox(f"{year}/1/1")
    autumn_date = ephem.Date(autumn).datetime().date()
    winter = ephem.next_winter_solstice(f"{year}/1/1")
    winter_date = ephem.Date(winter).datetime().date()
    for day, name in [
        (spring_date, "Spring Equinox"),
        (summer_date, "Summer Solstice"),
        (autumn_date, "Autumn Equinox"),
        (winter_date, "Winter Solstice"),
    ]:
        if day.year == year and day.month == month:
            events[day.day] = name
    return events


def get_all_special_dates(year, month, country, subdiv=None, timez=None):
    """
    Master function to call all other functions to generate a complete
    calendar with the text of all the special days of the month

    Args:
        year as int for the year
        month as int for the month (1~12)
        country as str for the initial of the country (CA, US, FR)
        subdiv as str for state/province/sub area
        timez as str for timezone
    """
    data = get_calendar_data(year, month)
    public = get_public_holidays(year, month, country, subdiv)
    astro = get_astronomical_events(year, month)
    dst = get_dst_transitions(year, month, timez) if timez else {}
    recurring = get_recurring_observances(month)
    easter_related = get_easter_related(year, month)
    merged_events =  merge_event_dicts(public, astro, dst, recurring, easter_related)
    render_calendar_image(data, merged_events)


# get_all_special_dates(2026, 4, "CA", subdiv="QC", timez="America/Montreal")
# get_all_special_dates(2026, 3, "FR", timez="Europe/Paris")
# get_all_special_dates(2026, 5, "US", subdiv="CA", timez="America/Los_Angeles")
