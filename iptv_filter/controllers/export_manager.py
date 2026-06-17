import os
from typing import List
from iptv_filter.models.channel import Channel

class ExportManager:
    @staticmethod
    def export_m3u(filepath: str, channels: List[Channel], include_offline: bool = True):
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")

            for ch in channels:
                if not ch.streams:
                    continue

                for stream in ch.streams:
                    # Basic attributes
                    attrs = []
                    attrs.append(f'tvg-id="{ch.id}"')
                    if ch.country:
                        attrs.append(f'tvg-country="{ch.country}"')
                    if ch.categories:
                        # usually takes the first or joined
                        attrs.append(f'group-title="{ch.categories[0]}"')

                    attr_str = " ".join(attrs)
                    f.write(f'#EXTINF:-1 {attr_str},{ch.name}\n')

                    # Write referer or user_agent if present
                    if stream.get("user_agent") or stream.get("referrer"):
                        vlcopts = []
                        if stream.get("user_agent"):
                            vlcopts.append(f'#EXTVLCOPT:http-user-agent={stream["user_agent"]}')
                        if stream.get("referrer"):
                            vlcopts.append(f'#EXTVLCOPT:http-referrer={stream["referrer"]}')
                        f.write("\n".join(vlcopts) + "\n")

                    f.write(f"{stream.get('url')}\n")
