import os
import sys
import json
import discord
import requests
import xmltodict
from discord.ext import commands
from dotenv import load_dotenv
import random
import feedparser

# loads .env
load_dotenv()
print(".env loaded")

# assigns vars to values in .env
maxPoints = int(os.getenv('maxPoints'))
token = os.getenv('dToken')
OPENWEATHER_API_KEY = os.getenv('openweatherapi')
ver = os.getenv('version')
print("vars assigned")

# stuff to deal with the api requests
OPENWEATHER_FORECAST_BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'
MET_BASE_URL = 'http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?'
MET_WEATHER_WARNINGS_BASE_URL = 'https://www.met.ie/warningsxml/rss.xml'
# relates to the jack command (making jack's life hard :>)
jack_bool = False
# standard bot initialization: currently using all intents until i figure out what all of
# what i want the finished bot to do
intents = discord.Intents.all()
bot = commands.Bot('$', intents=intents)


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user} with {bot.user.id} Version: {ver}")


@bot.listen('on_message')
# this listens for each message, and runs through the set of criteria listed
async def on_message(ctx):
    global jack_bool
    if ctx.author.id == bot.user.id:
        return
    elif ctx.author.id != bot.user.id:
        if ctx.content.find("gay spar") != -1:
            await ctx.reply('fruity', mention_author=True)
            await ctx.add_reaction('🏳️‍🌈')
        elif ctx.content.find("eddie") != -1:
            await ctx.reply('fucker', mention_author=True)
        elif ctx.content.find("fun fact") != -1:
            await ctx.add_reaction('👌')
            rand = random.randint(1, checkFunFactsLength())
            msg = weatherFunFact()
            output = msg[f'{rand}']
            await ctx.reply(output, mention_author=True)
        elif ctx.content.find("meteor") != -1:
            await ctx.add_reaction('☄️')
        elif ctx.content.find("snake") != -1:
            await ctx.add_reaction('🐍')
        elif ctx.content.find("smudge") != -1:
            if ctx.guild.id != 690691828307066930:
                return
            else:
                await ctx.reply('<:smudge:726830894371045466>')

        if ctx.author.id == 442008100392927233 & jack_bool:
            await ctx.reply('shut up bitch', mention_author=True)


@bot.command()
# basic test to see if the bot is there
async def hello(ctx: commands.Context):
    await ctx.send("Hello")


@bot.command()
async def snake(ctx: commands.Context):
    await ctx.message.add_reaction('🐍')


@bot.command()
# echos what the player says in arg
async def echo(ctx, arg='Tell me something to say back!'):
    await ctx.reply(arg)


@bot.command()
# this command disables or enables jack mode which ties in with the on_message listener
async def jack(ctx):
    if ctx.guild.id != 690691828307066930:
        return
    global jack_bool
    if not jack_bool:
        await ctx.reply("Jack mode enabled")
        jack_bool = True
    else:
        await ctx.reply("Jack mode disabled")
        jack_bool = False


@bot.command()
# gets a forecast from openweatherapi, parses the data and embeds it into a discord embed
async def forecast(ctx, arg='cobh'):
    data = get_openweather_forecast(arg)
    embed = openweatherDataToEmbed(data, arg)
    await ctx.send(embed=embed)


@bot.command()
# compare forecasts between two cities
async def compare(ctx, arg='cobh', arg2='vienna'):
    arg_data = get_openweather_forecast(arg)
    arg2_data = get_openweather_forecast(arg2)
    embed = comparisonEmbed(arg_data, arg2_data, arg, arg2)
    await ctx.send(embed=embed)


@bot.command()
# gets the current forecast for met eireann
async def met(ctx, arg='cobh', time=0):
    def check(reaction, user):
        return user == ctx.author and (
                str(reaction.emoji) == "📊" or "🌧️" or "☁️" or "⬅")

    async def metEdits(msg, dict):
        await msg.clear_reactions()
        await msg.edit(embed=dict['splash'])
        await msg.add_reaction('📊')
        await msg.add_reaction('🌧️')
        await msg.add_reaction('☁️')
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
        except TimeoutError:
            await msg.clear_reactions()
        else:
            if str(reaction.emoji) == '📊':
                await msg.edit(embed=embeds['expanded'])
                await msg.clear_reactions()
                await msg.add_reaction('⬅')
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
                except TimeoutError:
                    await msg.clear_reactions()
                else:
                    if str(reaction.emoji) == '⬅':
                        await metEdits(msg, embeds)
            elif str(reaction.emoji) == '🌧️':
                await msg.edit(embed=embeds['precip'])
                await msg.clear_reactions()
                await msg.add_reaction('⬅')
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
                except TimeoutError:
                    await msg.clear_reactions()
                else:
                    if str(reaction.emoji) == '⬅':
                        await metEdits(msg, embeds)
            elif str(reaction.emoji) == '☁️':
                await msg.edit(embed=embeds['cloud'])
                await msg.clear_reactions()
                await msg.add_reaction('⬅')
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
                except TimeoutError:
                    await msg.clear_reactions()
                else:
                    if str(reaction.emoji) == '⬅':
                        await metEdits(msg, embeds)

    if checkCity(arg):
        x = countCity(arg)
        output = findCityData(x)
        data = get_met_forecast(output[0], output[1])
        name = arg.capitalize()
        embeds = metDataToEmbed(data, output[0], output[1], name, time)
        msg = await ctx.send(embed=embeds['splash'])
        await metEdits(msg, embeds)
    else:
        await ctx.reply('Please specify a major Irish city.')


@bot.command()
async def git(ctx):
    # replies to the command with the repo
    await ctx.reply("https://github.com/howlism/weather-bot")


@bot.command()
async def mwarn(ctx):
    # gets weather warnings from met.ie
    data = get_met_warnings()
    print(len(data['entries']))
    for i in range(0, len(data['entries'])):
        link = data['entries'][i]['link']
        warning_data = get_warning_details(link)
        onset_time = warning_data['alert']['info']['onset']
        split_onset = onset_time.split('T')
        digits_onset = split_onset[1].removesuffix('-00:00')
        date_onset = split_onset[0].split('-')
        cleaned_date_onset = date_onset[2] + "/" + date_onset[1] + "/" + date_onset[0]
        expires_time = warning_data['alert']['info']['expires']
        split_expires = expires_time.split('T')
        digits_expires = split_expires[1].removesuffix('-00:00')
        date_expires = split_expires[0].split('-')
        cleaned_date_expires = date_expires[2] + "/" + date_expires[1] + "/" + date_expires[0]
        time_sent = warning_data['alert']['sent']
        split_sent = time_sent.split("T")
        digits_sent = split_sent[1].removesuffix('-00:00')
        date_sent = split_sent[0].split("-")
        cleaned_date_sent = date_sent[2] + "/" + date_sent[1] + "/" + date_sent[0]
        severity = warning_data['alert']['info']['severity']
        warning = warning_data['alert']['info']['event']
        if "Small Craft" in warning_data['alert']['info']['event']:
            warning = warning_data['alert']['info']['event'] + " <:small_craft_warning:1173727065548259358>"
        if 'Moderate' in warning_data['alert']['info']['severity']:
            severity = warning_data['alert']['info']['severity'] + ' 🟨'
        elif 'Severe' in warning_data['alert']['info']['severity']:
            severity = warning_data['alert']['info']['severity'] + ' 🟧'
        elif 'Extreme' in warning_data['alert']['info']['severity']:
            severity = warning_data['alert']['info']['severity'] + ' 🟥'
        warning_embed = discord.Embed(title=f"{warning_data['alert']['info']['headline']}",
                                      description=f"{warning_data['alert']['info']['description']}")
        warning_embed.add_field(name=f'Effective:', value=f'{cleaned_date_onset} @ {digits_onset} -> ' + '\n'
                                                                                                         f'{cleaned_date_expires} @ {digits_expires}')
        warning_embed.add_field(name="Type ⚠️:", value=f"{warning}")
        warning_embed.add_field(name="Severity:", value=f"{severity}")
        warning_embed.set_footer(text=f"Sent by: {warning_data['alert']['sender']} @ "
                                      f"{digits_sent} on {cleaned_date_sent}")
        await ctx.send(embed=warning_embed)


# bot help command
@bot.command()
async def whelp(ctx):
    def check(reaction, user):
        return user == ctx.author and (
                str(reaction.emoji) ==
                "1️⃣" or "2️⃣" or "3️⃣" or "4️⃣" or "5️⃣" or '6️⃣' or '7️⃣' or '⬅')

    def embedCreation():
        splash_help = discord.Embed(title="🌤️ Weather-Bot Help", description=f'List of currently supported commands!')
        splash_help.add_field(name='1. $echo (text)', value='Replies to your message with whatever the (text) is.')
        splash_help.add_field(name='2. $jack', value=f'Enables jack mode. Currently: {jack_bool}')
        splash_help.add_field(name='3. $forecast (city)',
                              value=f'Returns a forecast for any city in the world. Source: '
                                    f'OpenWeather. Default = Cobh')
        splash_help.add_field(name='4. $met (city) (time)',
                              value=f'Returns a forecast for any major city in Ireland. Source: Met Eireann. '
                                    f'Default: Cobh')
        splash_help.add_field(name='5. $git', value=f'Returns the link to the public repo! '
                                                    f'Report issues and check out the code there.')
        splash_help.add_field(name='6. $compare (city1) (city2)', value=f'Returns a comparison between two forecasts '
                                                                        f'for any two city in the world. Source: '
                                                                        f'OpenWeather. Defaults = Cobh, Vienna')
        splash_help.add_field(name='7. $mwarn', value=f'Returns all the Met.ie weather warnings currently in place.')
        splash_help.add_field(name='Need help with a specific command?', value='Click its corresponding '
                                                                               'number in the reactions!')
        splash_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        echo_help = discord.Embed(title="🌤️ $echo Help", description=f'Syntax and functionality for $echo!')
        echo_help.add_field(name='$echo (text)', value='Replies to your message with whatever the (text) is.')
        echo_help.add_field(name='text:', value=f'Item to return in reply. Default: Tell me something to say back!')
        echo_help.add_field(name='Example: ',
                            value=f'$echo Hello! returns: Hello!')
        echo_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        jack_help = discord.Embed(title='🌤️ $jack Help', description='Syntax and functionality for $jack!')
        jack_help.add_field(name='$jack', value=f'Enables jack mode. Currently: {jack_bool}')
        jack_help.add_field(name='Functionality:', value=f'Jack mode is specific to one server. IYKYK :>')
        jack_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        forecast_help = discord.Embed(title='🌤️ $forecast Help', description='Syntax and functionality for $forecast!')
        forecast_help.add_field(name='$forecast (city)', value=f'Returns a forecast for any city in the world. Source: '
                                                               f'OpenWeather. Default = Cobh')
        forecast_help.add_field(name='city:', value=f'City name.')
        forecast_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        met_help = discord.Embed(title='🌤️ $met Help', description='Syntax and functionality for $met!')
        met_help.add_field(name='$met (city) (time)',
                           value=f'Returns a forecast for any major city in Ireland. Source: Met Eireann. '
                                 f'Default: Cobh, 0hrs')
        met_help.add_field(name='city:', value=f'Major Irish city name.')
        met_help.add_field(name='time:', value=f'Retrieves the forecast in (time) hours.')
        met_help.add_field(name='Menus:', value=f'Clicking on the reactions to the message will change '
                                                f'the contents to a more specified output of data.')
        met_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        git_help = discord.Embed(title='🌤️ $git Help', description='Syntax and functionality for $git!')
        git_help.add_field(name='$git',
                           value='Returns the link to the public repo! Report issues and check out the code there.')
        git_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        compare_help = discord.Embed(title='🌤️ $compare Help', description='Syntax and functionality for $forecast!')
        compare_help.add_field(name='$compare (city1) (city2)', value=f'Returns a comparison between two forecasts '
                                                                      f'for any two city in the world. Source: '
                                                                      f'OpenWeather. Defaults = Cobh, Vienna')
        compare_help.add_field(name='city1, city2:', value=f'City name.')
        compare_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        warn_help = discord.Embed(title='🌤️ $mwarn Help', description='Syntax and functionality for $mwarn!')
        warn_help.add_field(name='$mwarn',
                            value='Returns all the Met.ie weather warnings currently in place.')
        warn_help.set_footer(text=f"Developed by howlism. Version: {ver}")
        return [splash_help, echo_help, jack_help, forecast_help, met_help, git_help, compare_help, warn_help]

    async def embedEdit(embed, arg, lst):
        await embed.edit(embed=lst[arg])
        await msg.add_reaction('⬅')
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
        except TimeoutError:
            await msg.clear_reactions()
        else:
            if str(reaction.emoji) == '⬅':
                await helpSplash(msg, embeds)

    async def helpSplash(msg, lst):
        await msg.clear_reactions()
        await msg.edit(embed=lst[0])
        await msg.add_reaction('1️⃣')
        await msg.add_reaction('2️⃣')
        await msg.add_reaction('3️⃣')
        await msg.add_reaction('4️⃣')
        await msg.add_reaction('5️⃣')
        await msg.add_reaction('6️⃣')
        await msg.add_reaction('7️⃣')
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=20.0, check=check)
        except TimeoutError:
            await msg.clear_reactions()
        else:
            if str(reaction.emoji) == '1️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 1, embeds)
            elif str(reaction.emoji) == '2️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 2, embeds)
            elif str(reaction.emoji) == '3️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 3, embeds)
            elif str(reaction.emoji) == '4️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 4, embeds)
            elif str(reaction.emoji) == '5️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 5, embeds)
            elif str(reaction.emoji) == '6️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 6, embeds)
            elif str(reaction.emoji) == '7️⃣':
                await msg.clear_reactions()
                await embedEdit(msg, 7, embeds)

    embeds = embedCreation()
    msg = await ctx.send(embed=embeds[0])
    await helpSplash(msg, embeds)


def get_openweather_forecast(location):
    # requests data from openweather, checks the request went properly, and returns the json data as data
    request_url = f'{OPENWEATHER_FORECAST_BASE_URL}?appid={OPENWEATHER_API_KEY}&q={location}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    else:
        print("request status is bad")


def get_met_forecast(lat, long):
    # requests data from met eireann, checks the request went properly and returns the json data as data
    # (converted from xml)
    request_url = f'{MET_BASE_URL}lat={lat};long={long}'
    print(request_url)
    response = requests.get(request_url)
    if response.status_code == 200:
        data = xmltodict.parse(response.content)
        return data
    else:
        print("request status is bad")


def get_met_warnings():
    # requests data from met eireann, checks the request went properly and returns the json data as data
    # (converted from xml)
    request_url = MET_WEATHER_WARNINGS_BASE_URL
    print(request_url)
    response = requests.get(request_url)
    if response.status_code == 200:
        data = feedparser.parse(MET_WEATHER_WARNINGS_BASE_URL)
        print(data)
        return data
    else:
        print("request status is bad")


def get_warning_details(link):
    request_url = link
    print(request_url)
    response = requests.get(request_url)
    if response.status_code == 200:
        data = xmltodict.parse(response.content)
        return data
    else:
        print("request status is bad")


def openweatherDataToEmbed(data, arg):
    # parses the important bits of the data from the data dict from openweather
    name = arg.capitalize()
    weather = data['weather'][0]['description'].capitalize()
    temperature = round(float(data['main']['temp']) - 273.15, 1)
    feels_like = round(float(data['main']['feels_like']) - 273.15, 1)
    country = data['sys']['country']
    lat, lon = data['coord']['lat'], data['coord']['lon']
    pressure = data['main']['pressure']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    wind_dir = data['wind']['deg']
    heading_name = calcPoint(wind_dir, 32)
    short_name = getShortName(heading_name)
    wind_speed_knots = round(wind_speed * 1.94384, 1)
    visibility = data['visibility']
    country_code = country.lower()
    title = f"Weather for {name} :flag_{country_code}:"
    embed = discord.Embed(title=title)
    embed.add_field(name="Weather description 📝:", value=weather, inline=False)
    embed.add_field(name="Avg. Temperature (Feels like) 🌡️:", value=f"{temperature}°C ({feels_like}°C)", inline=False)
    embed.add_field(name="Pressure 🕛:", value=f"{pressure}hPa", inline=False)
    embed.add_field(name="Humidity 💦:", value=f"{humidity}%", inline=False)
    embed.add_field(name="Visibility 👁️‍🗨️:", value=f"{visibility}m", inline=False)
    embed.add_field(name="Wind Speed ༄:", value=f"{wind_speed_knots}kts", inline=True)
    embed.add_field(name="Wind Dir 🧭:", value=f"{wind_dir}°, {short_name}", inline=True)
    embed.set_footer(text=f"Lat: {lat}, Lon: {lon}")
    return embed


def comparisonEmbed(data1, data2, name1, name2):
    Name1 = name1.capitalize()
    Name2 = name2.capitalize()
    weather1 = data1['weather'][0]['description'].capitalize()
    weather2 = data2['weather'][0]['description'].capitalize()
    temperature1 = round(float(data1['main']['temp']) - 273.15, 1)
    temperature2 = round(float(data2['main']['temp']) - 273.15, 1)
    feels_like1 = round(float(data1['main']['feels_like']) - 273.15, 1)
    feels_like2 = round(float(data2['main']['feels_like']) - 273.15, 1)
    country1 = data1['sys']['country']
    country2 = data2['sys']['country']
    wind_speed1 = data1['wind']['speed']
    wind_dir1 = data1['wind']['deg']
    heading_name1 = calcPoint(wind_dir1, 32)
    short_name1 = getShortName(heading_name1)
    wind_speed_knots1 = round(wind_speed1 * 1.94384, 1)
    wind_speed2 = data2['wind']['speed']
    wind_dir2 = data2['wind']['deg']
    heading_name2 = calcPoint(wind_dir2, 32)
    short_name2 = getShortName(heading_name2)
    wind_speed_knots2 = round(wind_speed2 * 1.94384, 1)
    country_code1 = country1.lower()
    country_code2 = country2.lower()
    title = f"Comparison for {Name1} :flag_{country_code1}: and {Name2} :flag_{country_code2}:"
    embed = discord.Embed(title=title)
    embed.add_field(name=f"Weather description for {Name1} 📝:", value=weather1, inline=True)
    embed.add_field(name=f"Weather description for {Name2} 📝:", value=weather2, inline=True)
    embed.add_field(name='', value='')
    embed.add_field(name=f"Avg. Temperature (Feels like) for {Name1} 🌡️:", value=f"{temperature1}°C ({feels_like1}°C)",
                    inline=True)
    embed.add_field(name=f"Avg. Temperature (Feels like) for {Name2} 🌡️:", value=f"{temperature2}°C ({feels_like2}°C)",
                    inline=True)
    embed.add_field(name='', value='')
    embed.add_field(name=f"Wind Speed for {Name1} ༄:", value=f"{wind_speed_knots1}kts", inline=True)
    embed.add_field(name=f"Wind Speed for {Name2} ༄:", value=f"{wind_speed_knots2}kts", inline=True)
    embed.add_field(name='', value='')
    embed.add_field(name=f"Wind Dir for {Name1} 🧭:", value=f"{wind_dir1}°, {short_name1}", inline=True)
    embed.add_field(name=f"Wind Dir for {Name2} 🧭:", value=f"{wind_dir2}°, {short_name2}", inline=True)
    embed.set_footer(text=f"Powered by Openweathermap.org")
    return embed


def metDataToEmbed(data, lat, long, name, time):
    time = time * 2
    # defines variables from met eireann forecast data
    data_type = data['weatherdata']['product']['time'][time]['@datatype']
    start_time = data['weatherdata']['product']['time'][time]['@from']
    end_time = data['weatherdata']['product']['time'][time]['@to']
    temp = data['weatherdata']['product']['time'][time]['location']['temperature']['@value']
    wind_dir = float(data['weatherdata']['product']['time'][time]['location']['windDirection']['@deg'])
    wind_speed, wind_beaufort = (data['weatherdata']['product']['time'][time]['location']['windSpeed']['@mps'],
                                 data['weatherdata']['product']['time'][time]['location']['windSpeed']['@beaufort'])
    wind_gust = data['weatherdata']['product']['time'][time]['location']['windGust']['@mps']
    global_rads, rads_unit = (data['weatherdata']['product']['time'][time]['location']['globalRadiation']['@value'],
                              data['weatherdata']['product']['time'][time]['location']['globalRadiation']['@unit'])
    humidity = data['weatherdata']['product']['time'][time]['location']['humidity']['@value']
    pressure = data['weatherdata']['product']['time'][time]['location']['pressure']['@value']
    cloud_cover = data['weatherdata']['product']['time'][time]['location']['cloudiness']['@percent']
    low_cloud, mid_cloud, high_cloud = (
        data['weatherdata']['product']['time'][time]['location']['lowClouds']['@percent'],
        data['weatherdata']['product']['time'][time]['location']['mediumClouds']['@percent'],
        data['weatherdata']['product']['time'][time]['location']['highClouds']['@percent'])
    dewpoint = data['weatherdata']['product']['time'][time]['location']['dewpointTemperature']['@value']
    rainfall_start_time = data['weatherdata']['product']['time'][time + 1]['@from']
    rainfall_end_time = data['weatherdata']['product']['time'][time + 1]['@to']
    avg_rainfall = data['weatherdata']['product']['time'][time + 1]['location']['precipitation']['@value']
    min_rainfall = data['weatherdata']['product']['time'][time + 1]['location']['precipitation']['@minvalue']
    max_rainfall = data['weatherdata']['product']['time'][time + 1]['location']['precipitation']['@maxvalue']
    prob = data['weatherdata']['product']['time'][time + 1]['location']['precipitation']['@probability']

    # cleans up variables for output
    heading_name = calcPoint(wind_dir, 32)
    short_name = getShortName(heading_name)
    wind_speed = float(wind_speed)
    wind_gust = float(wind_gust)
    wind_speed_knots = round(wind_speed * 1.94384, 1)
    wind_gust_knots = round(wind_gust * 1.94384, 1)
    cleaned_start_time = cleanMetTime(start_time)
    cleaned_end_time = cleanMetTime(end_time)
    cleaned_rain_start_time = cleanMetTime(rainfall_start_time)
    cleaned_rain_end_time = cleanMetTime(rainfall_end_time)
    DATA_TYPE = data_type.capitalize()

    # applies those variables in a discord embed
    # splash is the first embed that will appear when the command is called
    splash = discord.Embed(title=f"🇮🇪 Met Eireann {DATA_TYPE}, for {cleaned_start_time[0]} @ {cleaned_start_time[1]}"
                                 f" to {cleaned_end_time[0]} @ {cleaned_end_time[1]}.")
    splash.add_field(name='Temperature 🌡️:', value=f'{temp}°C')
    splash.add_field(name='Wind Direction 🧭:', value=f'{wind_dir}, {short_name}', inline=True)
    splash.add_field(name='Wind Speed ༄:', value=f'{wind_speed_knots}kts ({wind_gust_knots}kts)', inline=True)
    # splash.add_field(name='Wind Gust:', value=f'{wind_gust_knots}kts', inline=True)
    # splash.add_field(name='Beaufort:', value=f'Force {wind_beaufort}', inline=True)
    # splash.add_field(name='Humidity:', value=f'{humidity}%')
    # splash.add_field(name='Pressure:', value=f'{pressure}hPa')
    splash.add_field(name='Cloud Cover ☁️:', value=f'{cloud_cover}%')
    splash.add_field(name='Chance of Rain 🌧️:', value=f'{prob}%')
    splash.set_footer(text=f"{name} Lat: {lat}, Lon: {long}")

    # expanded is a more detailed version of splash
    expanded = discord.Embed(title=f"🇮🇪 Met Eireann {DATA_TYPE}, for {cleaned_start_time[0]} @ {cleaned_start_time[1]}"
                                   f" to {cleaned_end_time[0]} @ {cleaned_end_time[1]}.")
    expanded.add_field(name='Temperature 🌡️:', value=f'{temp}°C')
    expanded.add_field(name='Wind Direction 🧭:', value=f'{wind_dir}, {short_name}', inline=True)
    expanded.add_field(name='Wind Speed ༄:', value=f'{wind_speed_knots}kts', inline=True)
    expanded.add_field(name='Wind Gust ༄:', value=f'{wind_gust_knots}kts', inline=True)
    expanded.add_field(name='Beaufort 🌊:', value=f'Force {wind_beaufort}', inline=True)
    expanded.add_field(name='Global Radiation ☢️:', value=f'{global_rads}{rads_unit}')
    expanded.add_field(name='Humidity 💦:', value=f'{humidity}%')
    expanded.add_field(name='Pressure 🕛:', value=f'{pressure}hPa')
    expanded.add_field(name='Cloud Cover ☁️:', value=f'{cloud_cover}%')
    expanded.add_field(name='Dewpoint temperature 💧:', value=f'{dewpoint}°C')
    expanded.set_footer(text=f"{name} Lat: {lat}, Lon: {long}")

    # cloud is expanded data on clouds alone
    cloud = discord.Embed(title=f"🇮🇪 Met Eireann {DATA_TYPE}, for {cleaned_start_time[0]} @ {cleaned_start_time[1]}"
                                f" to {cleaned_end_time[0]} @ {cleaned_end_time[1]}.")
    cloud.add_field(name='Cloud Cover ☁️:', value=f'{cloud_cover}%')
    cloud.add_field(name='High Cloud Cover ☁️:', value=f'{high_cloud}%', inline=True)
    cloud.add_field(name='Mid Cloud Cover ☁️:', value=f'{mid_cloud}%', inline=True)
    cloud.add_field(name='Low Cloud Cover ☁️:', value=f'{low_cloud}%', inline=True)
    cloud.set_footer(text=f"{name} Lat: {lat}, Lon: {long}")

    # precip will be expanded data on precipitation
    precip = discord.Embed(title=f"🇮🇪 Met Eireann {DATA_TYPE}, for {cleaned_rain_start_time[0]} @ "
                                 f"{cleaned_rain_start_time[1]} to {cleaned_rain_end_time[0]} @ {cleaned_rain_end_time[1]}.")
    precip.add_field(name='Chance of Rain 🌧️:', value=f'{prob}%')
    precip.add_field(name='Average Rainfall 🌧️:', value=f'{avg_rainfall}mm', inline=True)
    precip.add_field(name='Min Rainfall 🌧️:', value=f'{min_rainfall}mm')
    precip.add_field(name='Max Rainfall 🌧️:', value=f'{max_rainfall}mm', inline=True)
    precip.set_footer(text=f"{name} Lat: {lat}, Lon: {long}")
    return {'splash': splash, 'expanded': expanded, 'cloud': cloud, 'precip': precip}


def metWarningsToEmbed(data):
    pass


def calcPoint(degHead, points):  # # credits to tony goodwin @ https://codegolf.stackexchange.com/questions/21927
    # /convert-degrees-to-one-of-the-32-points-of-the-compass#:~:text=Each%20direction%20is%2011.25%20(360,
    # and%20270%20degrees%20is%20W. for the code
    global maxPoints
    if points not in (8, 16, 32):
        sys.exit("not a good question")
    degHead = (degHead + (360 / points / 2)) / (360 / maxPoints)
    j = int(int(int(degHead % 8) % 8 / (maxPoints / points)) * maxPoints / points)
    degHead = int(degHead / 8) % 4
    cardinal = ['North', 'East', 'South', 'West']
    pointDesc = ['W', 'W by x', 'W-z', 'Z by w', 'Z', 'Z by x', 'X-z', 'X by w']  # vars not compass points
    W = cardinal[degHead]
    X = cardinal[(degHead + 1) % 4]
    w = W.lower()
    x = X.lower()
    if W == cardinal[0] or W == cardinal[2]:
        Z = W + x
    else:
        Z = X + w
    z = Z.lower()
    return (pointDesc[j].replace('W', W).replace('X', X).replace('w', w).replace('x', x)
            .replace('Z', Z).replace('z', z))


def cleanMetTime(string):
    split = string.split("T")
    # split[0] is date in YYYY-MM-DD
    # split[1] is time in hh:mm:ssZ
    rev_date = split[0].split("-")
    # date is now DD MM YYYY
    date = f"{rev_date[2]}/{rev_date[1]}/{rev_date[0]}"
    timeZ = split[1]
    time = timeZ[:-1]
    output = [date, time]
    return output


def checkCity(arg):
    count = 0
    with open('jsons/ie.json', 'r', encoding='utf-8') as file:
        out = json.load(file)
        for i in range(0, len(out)):
            data = out[i]['city']
            city_name = str(arg).capitalize()
            count += 1
            if city_name in data:
                return True
        return False


def countCity(arg):
    count = 0
    cwd = os.getcwd()
    with open(f'{cwd}/jsons/ie.json', 'r', encoding='utf-8') as file:
        out = json.load(file)
        for i in range(0, len(out)):
            data = out[i]['city']
            city_name = str(arg).capitalize()
            count += 1
            if city_name in data:
                return count - 1
        sys.exit("City not in dict")


def findCityData(num):
    cwd = os.getcwd()
    with open(f'{cwd}/jsons/ie.json', 'r', encoding='utf-8') as file:
        out = json.load(file)
        lat = out[num]['lat']
        long = out[num]['lng']
        output = [lat, long]
        return output


def getShortName(name):
    return name.replace('North', 'N').replace('East', 'E').replace('South', 'S').replace('West', 'W').replace('north',
                                                                                                              'N').replace(
        'east', 'E').replace('south', 'S').replace('west', 'W').replace('by', 'b').replace(' ', '').replace('-', '')


def checkFunFactsLength():
    cwd = os.getcwd()
    with open(f'{cwd}/jsons/funfacts.json', 'r') as file:
        out = json.load(file)
        keysLst = list(out.keys())
        return len(keysLst)


def weatherFunFact():
    cwd = os.getcwd()
    with open(f'{cwd}/jsons/funfacts.json', 'r') as file:
        out = json.load(file)
        return out


if __name__ == '__main__':
    bot.run(token)
