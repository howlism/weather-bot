import os
import sys
import json
import discord
import requests
import xmltodict
from discord.ext import commands
from dotenv import load_dotenv
import random

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
METEIREANN_BASE_URL = 'http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?'
# relates to the jack command (making jack's life hard :>)
jackBOOL = False
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
    global jackBOOL
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

        if ctx.author.id == 442008100392927233 & jackBOOL:
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
    global jackBOOL
    if not jackBOOL:
        await ctx.reply("Jack mode enabled")
        jackBOOL = True
    else:
        await ctx.reply("Jack mode disabled")
        jackBOOL = False


@bot.command()
# gets a forecast from openweatherapi, parses the data and embeds it into a discord embed
async def forecast(ctx, arg='cobh'):
    if arg:
        data = get_openweather_forecast(arg)
        embed = openweatherDataToEmbed(data, arg)
        await ctx.send(embed=embed)
    else:
        await ctx.reply("Please specify a city.")


@bot.command()
# gets the current forecast for met eireann
async def met(ctx, arg='cobh'):
    def check(reaction, user):
        return user == ctx.author and (
                str(reaction.emoji) == "📊" or "🌧️" or "☁️" or "⬅" or "5️⃣" or "6️⃣" or "7️⃣" or "8️⃣" or "9️⃣" or "➡️")

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
        embeds = metDataToEmbed(data, output[0], output[1], name)
        msg = await ctx.send(embed=embeds['splash'])
        await metEdits(msg, embeds)
    else:
        await ctx.reply('Please specify a major Irish city.')


@bot.command()
async def git(ctx):
    # replies to the command with the repo
    await ctx.reply("https://github.com/howlism/weather-bot")


# bot help command
@bot.command()
async def whelp(ctx):
    def check(reaction, user):
        return user == ctx.author and (
                str(reaction.emoji) ==
                "1️⃣" or "2️⃣" or "3️⃣" or "4️⃣" or "5️⃣" or "6️⃣" or "7️⃣" or "8️⃣" or "9️⃣" or "➡️" or '⬅')

    def embedCreation():
        splash_help = discord.Embed(title="🌤️ Weather-Bot Help", description=f'List of currently supported commands!')
        splash_help.add_field(name='1. $echo (arg)', value='Replies to your message with whatever the (arg) is.')
        splash_help.add_field(name='2. $jack', value=f'Enables jack mode. Currently: {jackBOOL}')
        splash_help.add_field(name='3. $forecast (arg)', value=f'Returns a forecast for any city in the world. Source: '
                                                               f'OpenWeather. Default = Cobh')
        splash_help.add_field(name='4. $met (arg)',
                              value=f'Returns a forecast for any major city in Ireland. Source: Met Eireann. '
                                    f'Default: Cobh')
        splash_help.add_field(name='5. $git', value=f'Returns the link to the public repo! '
                                                    f'Report issues and check out the code there.')
        splash_help.add_field(name='Need help with a specific command?', value='Click its corresponding '
                                                                               'number in the reactions!')
        splash_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        echo_help = discord.Embed(title="🌤️ $echo Help", description=f'Syntax and functionality for $echo!')
        echo_help.add_field(name='$echo (arg)', value='Replies to your message with whatever the (arg) is.')
        echo_help.add_field(name='arg', value=f'Item to return in reply. Default: Tell me something to say back!')
        echo_help.add_field(name='Example: ',
                            value=f'$echo Hello! returns: Hello!')
        echo_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        jack_help = discord.Embed(title='🌤️ $jack Help', description='Syntax and functionality for $jack!')
        jack_help.add_field(name='$jack', value=f'Enables jack mode. Currently: {jackBOOL}')
        jack_help.add_field(name='Functionality:', value=f'Jack mode is specific to one server. IYKYK :>')
        jack_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        forecast_help = discord.Embed(title='🌤️ $forecast Help', description='Syntax and functionality for $forecast!')
        forecast_help.add_field(name='$forecast (arg)', value=f'Returns a forecast for any city in the world. Source: '
                                                              f'OpenWeather. Default = Cobh')
        forecast_help.add_field(name='arg:', value=f'City name.')
        forecast_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        met_help = discord.Embed(title='🌤️ $met Help', description='Syntax and functionality for $met!')
        met_help.add_field(name='$met (arg)',
                           value=f'Returns a forecast for any major city in Ireland. Source: Met Eireann. '
                                 f'Default: Cobh')
        met_help.add_field(name='arg:', value=f'Major Irish city name.')
        met_help.add_field(name='Menus:', value=f'Clicking on the reactions to the message will change '
                                                f'the contents to a more specified output of data.')
        met_help.set_footer(text=f"Developed by howlism. Version: {ver}")

        git_help = discord.Embed(title='🌤️ $git Help', description='Syntax and functionality for $git!')
        git_help.add_field(name='$git',
                           value='Returns the link to the public repo! Report issues and check out the code there.')
        git_help.set_footer(text=f"Developed by howlism. Version: {ver}")
        return [splash_help, echo_help, jack_help, forecast_help, met_help, git_help]

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
    request_url = f'{METEIREANN_BASE_URL}lat={lat};long={long}'
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


def metDataToEmbed(data, lat, long, name):
    # defines variables from met eireann forecast data
    data_type = data['weatherdata']['product']['time'][0]['@datatype']
    start_time = data['weatherdata']['product']['time'][0]['@from']
    end_time = data['weatherdata']['product']['time'][0]['@to']
    temp = data['weatherdata']['product']['time'][0]['location']['temperature']['@value']
    wind_dir = float(data['weatherdata']['product']['time'][0]['location']['windDirection']['@deg'])
    wind_speed, wind_beaufort = (data['weatherdata']['product']['time'][0]['location']['windSpeed']['@mps'],
                                 data['weatherdata']['product']['time'][0]['location']['windSpeed']['@beaufort'])
    wind_gust = data['weatherdata']['product']['time'][0]['location']['windGust']['@mps']
    global_rads, rads_unit = (data['weatherdata']['product']['time'][0]['location']['globalRadiation']['@value'],
                              data['weatherdata']['product']['time'][0]['location']['globalRadiation']['@unit'])
    humidity = data['weatherdata']['product']['time'][0]['location']['humidity']['@value']
    pressure = data['weatherdata']['product']['time'][0]['location']['pressure']['@value']
    cloud_cover = data['weatherdata']['product']['time'][0]['location']['cloudiness']['@percent']
    low_cloud, mid_cloud, high_cloud = (
        data['weatherdata']['product']['time'][0]['location']['lowClouds']['@percent'],
        data['weatherdata']['product']['time'][0]['location']['mediumClouds']['@percent'],
        data['weatherdata']['product']['time'][0]['location']['highClouds']['@percent'])
    dewpoint = data['weatherdata']['product']['time'][0]['location']['dewpointTemperature']['@value']
    avg_rainfall = data['weatherdata']['product']['time'][1]['location']['precipitation']['@value']
    min_rainfall = data['weatherdata']['product']['time'][1]['location']['precipitation']['@minvalue']
    max_rainfall = data['weatherdata']['product']['time'][1]['location']['precipitation']['@maxvalue']
    prob = data['weatherdata']['product']['time'][1]['location']['precipitation']['@probability']

    # cleans up variables for output
    heading_name = calcPoint(wind_dir, 32)
    short_name = getShortName(heading_name)
    wind_speed = float(wind_speed)
    wind_gust = float(wind_gust)
    wind_speed_knots = round(wind_speed * 1.94384, 1)
    wind_gust_knots = round(wind_gust * 1.94384, 1)
    cleaned_start_time = cleanMetTime(start_time)
    cleaned_end_time = cleanMetTime(end_time)
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
    precip = discord.Embed(title=f"🇮🇪 Met Eireann {DATA_TYPE}, for {cleaned_start_time[0]} @ {cleaned_start_time[1]}"
                                 f" to {cleaned_end_time[0]} @ {cleaned_end_time[1]}.")
    precip.add_field(name='Chance of Rain 🌧️:', value=f'{prob}%')
    precip.add_field(name='Average Rainfall 🌧️:', value=f'{avg_rainfall}mm', inline=True)
    precip.add_field(name='Min Rainfall 🌧️:', value=f'{min_rainfall}mm')
    precip.add_field(name='Max Rainfall 🌧️:', value=f'{max_rainfall}mm', inline=True)
    precip.set_footer(text=f"{name} Lat: {lat}, Lon: {long}")
    return {'splash': splash, 'expanded': expanded, 'cloud': cloud, 'precip': precip}


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
