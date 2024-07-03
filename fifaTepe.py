import pandas as pd
import random
import time

# Excel dosyasından veri okuma
df = pd.read_excel('male_players.xlsx')

def select_random_team(df, positions_needed):
    selected_players = []
    selected_player_ids = set()  # Seçilen oyuncuları takip etmek için bir set
    
    for position, count in positions_needed.items():
        available_players = df[df['player_positions'] == position]
        available_players = available_players[~available_players.index.isin(selected_player_ids)]  # Zaten seçilen oyuncuları filtrele
        if len(available_players) < count:
            return None  # Yeterli oyuncu yoksa None döndür
        sampled_players = available_players.sample(count)
        selected_players.extend(sampled_players.to_dict('records'))
        selected_player_ids.update(sampled_players.index)  # Seçilen oyuncuları sete ekle
    
    return pd.DataFrame(selected_players)

def calculate_chemistry(players):
    players['Chemistry'] = 0  # Her oyuncunun başlangıç kimyası 0
    # Kulüp kimyası
    club_counts = players['club_team_id'].value_counts()
    for club, count in club_counts.items():
        if count >= 7:
            players.loc[players['club_team_id'] == club, 'Chemistry'] += 3
        elif count >= 4:
            players.loc[players['club_team_id'] == club, 'Chemistry'] += 2
        elif count >= 2:
            players.loc[players['club_team_id'] == club, 'Chemistry'] += 1
    # Uyruk kimyası
    nationality_counts = players['nationality_id'].value_counts()
    for nationality, count in nationality_counts.items():
        if count >= 8:
            players.loc[players['nationality_id'] == nationality, 'Chemistry'] += 3
        elif count >= 5:
            players.loc[players['nationality_id'] == nationality, 'Chemistry'] += 2
        elif count >= 2:
            players.loc[players['nationality_id'] == nationality, 'Chemistry'] += 1
    # Lig kimyası
    league_counts = players['league_id'].value_counts()
    for league, count in league_counts.items():
        if count >= 8:
            players.loc[players['league_id'] == league, 'Chemistry'] += 3
        elif count >= 5:
            players.loc[players['league_id'] == league, 'Chemistry'] += 2
        elif count >= 3:
            players.loc[players['league_id'] == league, 'Chemistry'] += 1
    # Her oyuncunun kimyasını maksimum 3 ile sınırla
    players['Chemistry'] = players['Chemistry'].clip(upper=3)
    # Toplam kimya
    total_chemistry = players['Chemistry'].sum()
    return total_chemistry

def calculate_team_overall_and_chemistry(team):
    chemistry = calculate_chemistry(team)
    overall = team['overall'].mean()  # overall
    return overall, chemistry

def hill_climbing_algorithm(df, max_overall, max_chemistry, max_iterations, positions_needed):
    # Rastgele başlangıç takımı oluştur
    start_time = time.time()
    x = -1
    current_team = select_random_team(df, positions_needed)
    if current_team is None:
        return None

    current_overall, current_chemistry = calculate_team_overall_and_chemistry(current_team)
    
    best_team = current_team.copy()
    best_overall = current_overall
    best_chemistry = current_chemistry

    iteration = 1
    while iteration < max_iterations:
        # Tüm oyuncuların toplam puanını hesapla (overall + chemistry)
        current_team['total_score'] = current_team['overall'] + current_team['Chemistry']
        min_total_score = current_team['total_score'].min()
        
        # Toplam puanı en düşük olan oyuncuyu bul
        candidate = current_team[current_team['total_score'] == min_total_score]
        if not candidate.empty:
            position_to_change = candidate['player_positions'].iloc[0]
            candidate_overall = candidate['overall'].iloc[0]
        else:
            position_to_change = random.choice(current_team['player_positions'].unique())
            candidate_overall = -1  # default value if no candidate is found

        # Mevcut oyuncunun overall değerinden daha yüksek oyuncuları seç
        available_players = df[(df['player_positions'] == position_to_change) & (df['overall'] > candidate_overall)]
        available_players = available_players[~available_players['player_id'].isin(current_team['player_id'])]  # Duplicate olmayan oyuncuları seç

        if not available_players.empty:
            new_player = available_players.sample(1).to_dict('records')[0]
            replace_index = candidate.index[0]
            for key in new_player.keys():
                current_team.at[replace_index, key] = new_player[key]

            neighbor_overall, neighbor_chemistry = calculate_team_overall_and_chemistry(current_team)
            if neighbor_overall + neighbor_chemistry > current_chemistry + current_overall:
                current_overall, current_chemistry = neighbor_overall, neighbor_chemistry
                # En iyi takım ve skorları güncelle
                if current_overall + current_chemistry > best_overall + best_chemistry:
                    best_team = current_team.copy()
                    best_overall = current_overall
                    best_chemistry = current_chemistry

        # Her iterasyonda overall ve kimyayı yazdır
        print(f'Iteration {iteration + 1}: Overall: {current_overall}, Chemistry: {current_chemistry}')
        iteration += 1
        if x == -1:
            # Hedef değerlere ulaşıldıysa döndür
            if best_overall >= max_overall and best_chemistry >= max_chemistry:
                print(f'Target reached in {iteration + 1} iterations')
                print(f'Overall: {best_overall}, Chemistry: {best_chemistry}')
                print(best_team)
                x = int(input("Hedef takıma ulaşıldı. Devam etmek isterseniz 1, Çıkmak için 0 tuşlayınız."))
                if x == 0:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f"Kodun çalıştığı süre: {elapsed_time} saniye")
                    return best_team
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Kodun çalıştığı süre: {elapsed_time} saniye")
    return best_team

# Kullanıcıdan max overall ve max kimya parametrelerini alma
max_overall = int(input("Minimum overall değerini girin: "))
max_chemistry = int(input("Minimum kimya değerini girin: "))
max_iterations = int(input("Maximum iterasyon sayısını girin: "))

print("4-4-2 için 1 giriniz.\n4-3-3 için 2 giriniz.\n4-2-3-1 için 3 giriniz.\n4-5-1 için 4 giriniz.\n4-3-2-1 için 5 giriniz.")
dizilis = int(input("Lütfen Dizilis Seçiniz: "))

if dizilis == 1:
    positions_needed = {'GK': 1, 'RB': 1, 'CB': 2, 'LB': 1, 'RM': 1, 'CM': 2, 'LM': 1, 'ST': 2}
elif dizilis == 2:
    positions_needed = {'GK': 1, 'RB': 1, 'CB': 2, 'LB': 1, 'CDM': 1, 'CM': 2, 'LW': 1, 'RW': 1, 'ST': 1}
elif dizilis == 3:
    positions_needed = {'GK': 1, 'RB': 1, 'CB': 2, 'LB': 1, 'CDM': 1, 'CM': 1, 'CAM': 1, 'LW': 1, 'RW': 1, 'ST': 1}
elif dizilis == 4:
    positions_needed = {'GK': 1, 'RB': 1, 'CB': 2, 'LB': 1, 'CM': 1, 'LM': 1, 'RM': 1, 'CAM': 2, 'ST': 1}
elif dizilis == 5:
    positions_needed = {'GK': 1, 'RB': 1, 'CB': 2, 'LB': 1, 'CM': 3, 'ST': 3}
else:
    print("Geçersiz seçim. Lütfen geçerli bir seçim yapınız.")

# Tepe tırmanma algoritmasını çalıştırma
best_team = hill_climbing_algorithm(df, max_overall, max_chemistry, max_iterations, positions_needed)

best_overall, best_chemistry = calculate_team_overall_and_chemistry(best_team)
print(f'Best Team Overall: {best_overall}')
print(f'Best Team Chemistry: {best_chemistry}')
print(best_team)
