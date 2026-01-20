from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from geopy.distance import distance
from nostr_sdk import *
import geohash2
import asyncio
import random
import csv

# Configuration
RELAY_CSV_FILE = "online_relays_gps.csv"
MAX_OLD_MESSAGES = 20
MAX_TIME_DELAY = 5 * 60
TELEPORT = False

# Initialize values
GEO = ""
NAME = f"anon{random.randint(1000, 9999)}"
BLOCKED = set()

def closest_relays():
    # Read relay file
    relays = []
    with open(RELAY_CSV_FILE) as f:
        for row in csv.reader(f):
            if len(row) < 3: continue
            try:
                relays.append((row[0], float(row[1]), float(row[2])))
            except ValueError:
                continue
    # Return closest relays
    center = geohash2.decode(GEO)[:2]
    sorted_relays = sorted(relays, key=lambda r: distance(center, r[1:]).km)
    return set(RelayUrl.parse(f"wss://{url}") for url, *_ in sorted_relays[:5])

class NotificationHandler(HandleNotification):
    def __init__(self):
        self.oldMessages = []
        self.eoseRelays = set()

    def remove_relay(self, relay):
        # Removes a relay from eoseRelays, gets called when relay is disconnected
        if relay in self.eoseRelays:
            self.eoseRelays.remove(relay)

    async def handle_msg(self, relay_url, msg):
        if msg.as_enum().is_end_of_stored_events():
            # Add relay to eoseRelays once EOSE is received
            self.eoseRelays.add(relay_url)
            if len(self.eoseRelays) >= 3 and self.oldMessages:
                # If enough relays have sent all stored events then display them
                for name, message in reversed(self.oldMessages):
                    print(f"<{name}>: {message}", flush=True)
                self.oldMessages.clear()

    async def handle(self, relay_url, subscription_id, event: Event):
        # Ignore events that are older than MAX_TIME_DELAY
        if event.created_at().as_secs() < Timestamp.now().as_secs() - MAX_TIME_DELAY:
            return
        # Ignore events from blocked authors
        if event.author().to_hex() in BLOCKED:
            return
        # Get tags
        tags = [t.as_vec() for t in event.tags().to_vec()]
        tag_map = {t[0]: t[1] for t in tags if len(t) >= 2 and isinstance(t[1], str)}
        geo_tag, name_tag = tag_map.get("g"), tag_map.get("n")
        # Ingnore events from other channels
        if geo_tag != GEO:
            return
        # Store or display the message
        if len(self.eoseRelays) < 3:
            # If not enough relays have sent EOSE yet then store the message
            self.oldMessages.append((name_tag, event.content()))
        elif relay_url in self.eoseRelays:
            # If enough relays have sent EOSE and this relay is one of them then print
            print(f"<{name_tag}>: {event.content()}", flush=True)

async def send_message(client, text):
    # Create event
    builder = EventBuilder(Kind(20000), text).tags([
        Tag.parse(["g", GEO]),
        Tag.parse(["n", NAME])
    ])
    # Optional teleport tag
    if TELEPORT:
        builder.tags([Tag.parse(["t", "teleport"])])
    # Send event
    await client.send_event_builder(builder)

async def connect_geohash(client, notification_handler):
    # Update relays
    current_relays = set(await client.relays())
    next_relays = closest_relays()
    new_relays = next_relays - current_relays
    for relay in current_relays - next_relays:
        await client.remove_relay(relay)
        notification_handler.remove_relay(relay)
    for relay in new_relays:
        await client.add_relay(relay)
    # Create message filter
    bc_filter = Filter().kind(Kind(20000)).limit(MAX_OLD_MESSAGES)
    # Connect and subscribe
    await client.connect()
    await client.subscribe_to(new_relays, bc_filter, None)

async def main():
    global GEO, NAME
    # UI
    session = PromptSession(
        lambda: f"<{NAME}>: ",
        style=Style.from_dict({'prompt': 'bold orange'}),
        multiline=False
    )
    print("Commands: /geo /name /quit")
    # Generate keys
    client = Client(NostrSigner.keys(Keys.generate()))
    # NotificationHandler
    notification_handler = NotificationHandler()
    asyncio.create_task(client.handle_notifications(notification_handler))
    # Connect if GEO is set in script
    if GEO:
        await connect_geohash(client, notification_handler)
    # Input loop
    with patch_stdout():
        while True:
            try:
                # Get input
                text = await session.prompt_async()
                text = text.strip()
                # "/geo" command switches location channels
                if text.lower().startswith("/geo "):
                    new_geo = text[5:].strip()
                    if new_geo and new_geo != GEO:
                        GEO = new_geo
                        await connect_geohash(client, notification_handler)
                # "/name" command changes the username
                elif text.lower().startswith("/name "):
                    new_name = text[6:].strip()
                    if new_name:
                        NAME = new_name
                # "/quit" command quits the program
                elif text.lower().startswith("/quit"):
                    break
                # If no command then send text
                elif text and GEO:
                    asyncio.create_task(send_message(client, text))
            except (EOFError, KeyboardInterrupt):
                break

if __name__ == '__main__':
    asyncio.run(main())