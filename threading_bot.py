import asyncio
import discord
from discord.ui import Select, View
from discord.ext import commands
import json

from threading import Thread

openfile = open('config.json', 'r')
configs = json.load(openfile)

dc_token1 = configs['token1']
dc_token2 = configs['token2']
dc_vc_id1 = None
dc_vc_id2 = None

client = discord.Client(intents=discord.Intents.all())
sub_client = discord.Client(intents=discord.Intents.all())

Queue = asyncio.Queue()

def init():
    loop1 = asyncio.get_event_loop()
    loop1.create_task(client.start(dc_token1))
    job1 = Thread(target=loop1.run_forever)

    loop2 = asyncio.get_event_loop()
    loop2.create_task(sub_client.start(dc_token2))
    job2 = Thread(target=loop2.run_forever)


    job1.start()
    job2.start()

    job1.join()
    job2.join()


@client.event
# 準備完了
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
# イベント作成時にシステムチャンネルに通知
async def on_scheduled_event_create(event):
    await event.guild.system_channel.send(f'{event.name}が作成されました!!イベントをチェック!!' + event.url)

@client.event
async def on_voice_state_update(member, before, after):
     
    # チャンネルへの入室ステータスが変更されたとき（ミュートON、OFFに反応しないように分岐）
    if before.channel != after.channel:
        # 通知メッセージを書き込むテキストチャンネル（system_channel）
        sysch = member.guild.system_channel
 
        # 退室通知
        if before.channel is not None:
            print("" + before.channel.name + " から、" + member.name + "  が抜けました！")
            #sys.exit()
            #await botRoom.send("" + before.channel.name + " から、" + member.name + "  が抜けました！")
        # 入室通知
        if not before.channel and after.channel and len(after.channel.members) == 1:
            #print(member.voice.channel.members.size)
            Invite = await after.channel.create_invite()
            await sysch.send(after.channel.name + "で" + member.name + "が待っています" + Invite.url)
            print(after.channel.name + "で" + member.name + "が待っています" + Invite.url)


@client.event
# 以下、コマンド受け取り時の処理
async def on_message(message):
    if message.author == client.user:
        return

    # 「--expend」は聞きたいボイスチャンネルの音声取得
    if message.content.startswith('--expend'):

        if message.author.voice is None:
                await message.channel.send('ボイスチャンネルに参加してからコマンドを打ってください。')
                return
        if(message.guild.voice_client == None):
            # ボイスチャンネルIDが未指定なら
            if dc_vc_id1 == None:
                await message.author.voice.channel.connect()
            # ボイスチャンネルIDが指定されていたら
            else:
                await client.get_channel(dc_vc_id1).connect()
        # 接続済みか確認
        elif(message.guild.voice_client.is_connected() == True):
            # ボイスチャンネルIDが未指定なら
            if dc_vc_id1 == None:
                await message.guild.voice_client.move_to(message.author.voice.channel)
            # ボイスチャンネルIDが指定されていたら
            else:
                await message.guild.voice_client.move_to(client.get_channel(dc_vc_id1))

        # voice_channelの取得と提示用リスト作成
        channels = message.guild.voice_channels
        args = {}
        for channel in channels:
            args.setdefault(channel.name, channel.id)
        options=[]
        for item in args:
            options.append(discord.SelectOption(label=item, description=''))

        select_menu = Select(placeholder='channels', options=options)

        async def menu_callback(Interaction):
            await Queue.put(args[select_menu.values[0]])
            await Interaction.channel.send(f'{Interaction.user.name}は{select_menu.values[0]}を選択しました')
            await message.channel.send('wakeup EAR')
            return

        
        select_menu.callback = menu_callback
        view = View()
        view.add_item(select_menu)
        await message.channel.send('choose channel', view=view)

    elif message.content.startswith('--team'):

        channels = message.guild.voice_channels
        args = {}
        for channel in channels:
            args.setdefault(channel.name, channel.id)
        options=[]
        for item in args:
            options.append(discord.SelectOption(label=item, description=''))

        select_menu = Select(placeholder='channels', options=options)

        async def menu_callback(Interaction):
            team = client.get_channel(args[select_menu.values[0]])
            await Interaction.user.move_to(team)

        select_menu.callback = menu_callback
        view = View()
        view.add_item(select_menu)
        await message.channel.send('choose channel', view=view)

        
        
    elif message.content.startswith('--bye'):
        if message.guild.voice_client is None:
            await message.channel.send('僕はまだそこにいないよ')
            return

        await message.guild.voice_client.disconnect()


@sub_client.event
async def on_ready():
    print(f'We have logged in as {sub_client.user}')

@sub_client.event
async def on_message(message):
    if message.author == sub_client.user:
        return

    if message.author == client.user:
        if message.content.startswith('wakeup EAR'):
            channel = await Queue.get()
            await sub_client.get_channel(channel).connect()
            await message.channel.send('hi')

            
        
    elif message.content.startswith('--bye'):
        if message.guild.voice_client is None:
            await message.channel.send('僕はまだそこにいないよ')
            return

        else:
            await message.guild.voice_client.disconnect()

init()
