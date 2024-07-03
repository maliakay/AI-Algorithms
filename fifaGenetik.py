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

def calculate_team_fitness(team, max_overall, max_chemistry):
    overall, chemistry = calculate_team_overall_and_chemistry(team)
    # Overall ve kimya hedeflerine ne kadar yakınsa o kadar iyi
    overall_score = overall / max_overall
    chemistry_score = min(chemistry, max_chemistry) / max_chemistry
    # Fitness skoru, her iki özelliğin de hedefe ne kadar yakın olduğunu dikkate alarak hesaplanır
    fitness = overall_score * 0.7 + chemistry_score * 0.3  # Her iki skorun ağırlıklı ortalaması
    return fitness

def genetic_algorithm(df, max_overall, max_chemistry, generations, positions_needed, population_size=100, crossover_prob=0.7, mutation_prob=0.1):
    # İlk popülasyonu oluştur
    start_time = time.time()
    population = [select_random_team(df, positions_needed) for _ in range(population_size)]
    population = [team for team in population if team is not None]  # None olmayanları seç
    x= -1

    for generation in range(generations):
        # Fitness hesapla
        fitness_scores = []
        for team in population:
            fitness = calculate_team_fitness(team, max_overall, max_chemistry)
            fitness_scores.append((fitness, team))

        # Fitness'a göre sırala
        fitness_scores.sort(reverse=True, key=lambda x: x[0])
        
        # En iyi bireyleri seç
        selected = [team for _, team in fitness_scores[:population_size // 2]]

        # Yeni popülasyon oluştur (crossover ve mutasyon)
        new_population = selected.copy()
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(selected, 2)
            
            # Çaprazlama
            if random.random() < crossover_prob:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()
            
            # Mutasyon
            mutate(child1, df, positions_needed)
            mutate(child2, df, positions_needed)
            
            new_population.extend([child1, child2])

        population = new_population[:population_size]

        # En iyi bireyi yazdır
        best_fitness, best_team = fitness_scores[0]
        best_overall, best_chemistry = calculate_team_overall_and_chemistry(best_team)
        print(f'Generation {generation + 1}: Best Overall: {best_overall}, Best Chemistry: {best_chemistry}')
        
        if x == -1:
                # Hedef değerlere ulaşıldıysa döndür
            if best_overall >= max_overall and best_chemistry >= max_chemistry:
                print(f'Target reached in {generation + 1} iterations')
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

def crossover(parent1, parent2):
    # Tek noktalı crossover
    crossover_point = random.randint(1, len(parent1) - 1)
    child1_data = pd.concat([parent1.iloc[:crossover_point], parent2.iloc[crossover_point:]])
    child2_data = pd.concat([parent2.iloc[:crossover_point], parent1.iloc[crossover_point:]])
    return child1_data.reset_index(drop=True), child2_data.reset_index(drop=True)

def mutate(child, df, positions_needed):
    # Takıma katkısı en az olan oyuncuyu belirle (overall + kimya skoru)
    child['total_score'] = child['overall'] + child['Chemistry']
    min_total_score = child['total_score'].min()
    candidate = child[child['total_score'] == min_total_score]
    
    if not candidate.empty:
        position_to_change = candidate['player_positions'].iloc[0]
        candidate_overall = candidate['overall'].iloc[0]
        
        # Mevcut oyuncunun overall değerinden daha yüksek oyuncuları seç
        available_players = df[(df['player_positions'] == position_to_change) & (df['overall'] > candidate_overall)]
        available_players = available_players[~available_players['player_id'].isin(child['player_id'])] 
        if not available_players.empty:
            new_player = available_players.sample(1).to_dict('records')[0]
            replace_index = candidate.index[0]
            for key in new_player.keys():
                child.at[replace_index, key] = new_player[key]


# Kullanıcıdan max overall ve max kimya parametrelerini alma
max_overall = int(input("Minimum overall değerini girin: "))
max_chemistry = int(input("Minimum kimya değerini girin: "))
generation_param = int(input("Generation sayısı gir : "))

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

# Genetik algoritmayı çalıştırma

best_team = genetic_algorithm(df, max_overall, max_chemistry, generation_param, positions_needed)


best_overall, best_chemistry = calculate_team_overall_and_chemistry(best_team)
print(f'Best Team Overall: {best_overall}')
print(f'Best Team Chemistry: {best_chemistry}')
print(best_team)
