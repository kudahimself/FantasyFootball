from datetime import datetime
import aiohttp
from fpl import FPL
import asyncio
import pandas as pd
import os


async def get_current_gw_player_details():
    async with aiohttp.ClientSession() as session:
        fpl = FPL(session)
        gameweeks = await fpl.get_gameweeks()
        # current_gw = next(gw for gw in gameweeks if gw.is_current)
        # prev_gw = next((gw for gw in reversed(gameweeks) if gw.id < current_gw.id), None)
        # gw_id = prev_gw.id if prev_gw else current_gw.id
        gameweeks = await fpl.get_gameweeks()
        current_gw = next(gw for gw in gameweeks if gw.is_current)
        gw_id = current_gw.id
        players = await fpl.get_players()
        rows = []
        for player in players:
            history = await fpl.get_player_summary(player.id)
            gw_entry = None
            for g in history.history:
                if 'event' in g and g['event'] == gw_id:
                    gw_entry = g
                    break
                elif 'round' in g and g['round'] == gw_id:
                    gw_entry = g
                    break
            if gw_entry:
                rows.append({
                    "Player": f"{player.first_name} {player.second_name}",
                    "Date": gw_entry.get('kickoff_time', None),
                    "Comp": "Premier League",
                    "Round": gw_entry.get('event', gw_entry.get('round', None)),
                    "Opponent": gw_entry.get('opponent_team', None),
                    "Result": gw_entry.get('result', None),
                    "Min": gw_entry.get('minutes', None),
                    "Gls": gw_entry.get('goals_scored', None),
                    "Ast": gw_entry.get('assists', None),
                    'was_home': gw_entry.get('was_home', None),
                    'team_a_score': gw_entry.get('team_a_score', None),
                    'team_h_score': gw_entry.get('team_h_score', None)
                })
        df = pd.DataFrame(rows)
        # Convert 'Date' column from ISO format with time to just date (YYYY-MM-DD)
        df['Date'] = df['Date'].apply(lambda x: datetime.fromisoformat(x.replace("Z", "")).date() if isinstance(x, str) else x)
        return df

# Example usage:
async def main():
    df = await get_current_gw_player_details()
    df['Season'] = '2025-2026'
    df['Comp'] = 'Premier League'
    df['Result'] = df.apply(lambda x: f"{x['team_h_score']}-{x['team_a_score']}" if x['was_home'] else f"{x['team_a_score']}-{x['team_h_score']}", axis=1)
    df['Result'] = df['Result'].apply(lambda x: str(x) if pd.notnull(x) else x)
    df['Pos'] = None
    df['Elo'] = 0

    for _, row in df.iterrows():
        player_name = row['Player']
        player_file = f"./elo_data/{player_name.replace(' ', '_')}.csv"
        
        new_player_data = df[df['Player'] == player_name].copy()
        # Only select columns that exist in df
        columns_to_select = [col for col in ['Season', 'Date','Comp', 'Round', 'Opponent', 'Result', 'Pos', 'Min', 'Gls', 'Ast', 'Points', 'Elo'] if col in df.columns]
        new_player_data = new_player_data[columns_to_select]
        
        if os.path.exists(player_file):
            player_df = pd.read_csv(player_file)
            player_df = pd.concat([player_df, new_player_data], ignore_index=True)
        
            # Overwrite the old file with the updated DataFrame
            player_df['Date'] = pd.to_datetime(player_df['Date']).dt.date
            player_df = player_df.sort_values(by=['Date'])
            player_df['Result'] = player_df['Result'].apply(lambda x: str(x) if pd.notnull(x) else x)
            dedup_columns = [col for col in ['Season', 'Date'] if col in player_df.columns]
            # Keep the last occurrence to ensure the most recent data for each player/season/date is retained
            player_df.drop_duplicates(subset=dedup_columns, keep='last', inplace=True)
            if not player_df.empty:
                player_df.to_csv(player_file, index=False)
        else:
            print(f"File for {player_name} does not exist.")

if __name__ == "__main__":
    asyncio.run(main())

