import random
import time
from collections import deque

# Constantes para a grade
# 0: Vazio
# 1: Branco (White - ○)
# 2: Preto (Black - ■)

class HeyawakeSolver:
    def __init__(self, size=8):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.regions = []
        self.region_map = [[-1 for _ in range(size)] for _ in range(size)]
        self.attempts = 0
        self.backtracks = 0
        self.generate_puzzle()
    
    def generate_puzzle(self):
        """Gera regiões retangulares cobrindo todo o tabuleiro com constraints balanceadas"""
        region_id = 0
        cells_used = [[False for _ in range(self.size)] for _ in range(self.size)]
        
        for i in range(self.size):
            for j in range(self.size):
                if not cells_used[i][j]:
                    max_width = self.size - j
                    max_height = self.size - i
                    
                    # Tenta criar um retângulo maior (máx 4x4)
                    width = random.randint(1, min(4, max_width))
                    height = random.randint(1, min(4, max_height))
                    
                    actual_width = 0
                    actual_height = 0
                    
                    # Determina a largura máxima real
                    for w in range(1, width + 1):
                        if j + w - 1 < self.size and not cells_used[i][j + w - 1]:
                            actual_width = w
                        else:
                            break
                            
                    # Determina a altura máxima real
                    for h in range(1, height + 1):
                        row_ok = True
                        if i + h - 1 < self.size:
                            for c in range(j, j + actual_width):
                                if cells_used[i + h - 1][c]:
                                    row_ok = False
                                    break
                            if row_ok:
                                actual_height = h
                            else:
                                break
                        else:
                            break
                    
                    width = actual_width if actual_width > 0 else 1
                    height = actual_height if actual_height > 0 else 1
                    
                    # Garante que é no mínimo 1x1
                    if width == 0 or height == 0:
                        width = 1
                        height = 1

                    region_cells = []
                    for r in range(i, i + height):
                        for c in range(j, j + width):
                            if r < self.size and c < self.size and not cells_used[r][c]:
                                cells_used[r][c] = True
                                self.region_map[r][c] = region_id
                                region_cells.append((r, c))
                    
                    if not region_cells:
                        continue 
                        
                    region_size = len(region_cells)
                    
                    # 🔥 NOVA LÓGICA: Probabilidade dinâmica baseada no tamanho do tabuleiro
                    # Tabuleiros maiores = mais constraints
                    constraint = -1
                    
                    if region_size > 1:  # Só coloca constraint em regiões com 2+ células
                        # Probabilidade escalonada:
                        # 4x4 (16 células) → ~40% de chance
                        # 6x6 (36 células) → ~50% de chance
                        # 8x8 (64 células) → ~60% de chance
                        # 10x10 (100 células) → ~70% de chance
                        
                        base_probability = 0.35
                        size_factor = (self.size - 4) / 6  # Normaliza entre 0 (tamanho 4) e 1 (tamanho 10)
                        probability = min(0.75, base_probability + (0.35 * size_factor))
                        
                        if random.random() < probability:
                            # Gera constraint inteligente baseada no tamanho da região
                            # Regiões maiores podem ter mais pretos
                            if region_size <= 2:
                                max_blacks = 1
                            elif region_size <= 4:
                                max_blacks = min(2, region_size // 2)
                            elif region_size <= 6:
                                max_blacks = min(3, region_size // 2)
                            else:
                                max_blacks = min(4, region_size // 2)
                            
                            # Gera valor entre 0 e max_blacks
                            constraint = random.randint(0, max_blacks)
                    
                    self.regions.append({
                        'id': region_id,
                        'cells': region_cells,
                        'constraint': constraint
                    })
                    region_id += 1
        
        total_cells = sum(len(r['cells']) for r in self.regions)
        assert total_cells == self.size * self.size
    
    def is_valid_placement(self, row, col, value):
        """
        REGRA 1 (CRÍTICA): Células pretas NÃO podem ser adjacentes ortogonalmente
        """
        if value == 2:  # Tentando colocar PRETO
            for dr, dc in [(-1,0), (0,1), (1,0), (0,-1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.grid[nr][nc] == 2:
                        return False
        return True
    
    def check_no_adjacent_blacks(self):
        """REGRA 1: Verifica TODO o tabuleiro"""
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 2:
                    for dr, dc in [(-1,0), (0,1), (1,0), (0,-1)]:
                        ni, nj = i + dr, j + dc
                        if 0 <= ni < self.size and 0 <= nj < self.size:
                            if self.grid[ni][nj] == 2:
                                return False
        return True
    
    def check_region_constraint(self, region_id):
        """REGRA 3: Verifica constraints numéricas (parcial/preditiva)"""
        region = self.regions[region_id]
        if region['constraint'] < 0:
            return True
        
        black_count = 0
        empty_count = 0
        
        for r, c in region['cells']:
            if self.grid[r][c] == 2:
                black_count += 1
            elif self.grid[r][c] == 0:
                empty_count += 1
        
        if black_count > region['constraint']:
            return False
        
        if black_count + empty_count < region['constraint']:
            return False
        
        return True
    
    def check_white_connectivity_partial(self):
        """REGRA 2: Verifica conectividade parcial"""
        white_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 1:
                    white_cells.append((i, j))
        
        if len(white_cells) <= 1:
            return True
        
        visited = [[False for _ in range(self.size)] for _ in range(self.size)]
        queue = deque([white_cells[0]])
        visited[white_cells[0][0]][white_cells[0][1]] = True
        reachable_white_cells = 0
        
        while queue:
            r, c = queue.popleft()
            
            if self.grid[r][c] == 1:
                reachable_white_cells += 1
                
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if not visited[nr][nc]:
                        if self.grid[nr][nc] == 1 or self.grid[nr][nc] == 0:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                            
        return reachable_white_cells == len(white_cells)
    
    def check_white_connectivity_final(self):
        """REGRA 2: Validação FINAL"""
        white_cells = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == 1:
                    white_cells.append((i, j))
        
        if not white_cells:
            return False 
        
        visited = [[False for _ in range(self.size)] for _ in range(self.size)]
        queue = deque([white_cells[0]])
        visited[white_cells[0][0]][white_cells[0][1]] = True
        count = 1
        
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if not visited[nr][nc] and self.grid[nr][nc] == 1:
                        visited[nr][nc] = True
                        queue.append((nr, nc))
                        count += 1
        
        return count == len(white_cells)
    
    def check_white_line_regions_partial(self, r, c):
        """REGRA 4: Verificação parcial"""
        if self.grid[r][c] != 1: return True

        # Horizontal
        regions_h = set()
        start_c = c
        while start_c >= 0 and self.grid[r][start_c] == 1:
            start_c -= 1
        start_c += 1
        
        temp_c = start_c
        while temp_c < self.size and self.grid[r][temp_c] == 1:
            regions_h.add(self.region_map[r][temp_c])
            temp_c += 1
            
        if len(regions_h) > 2:
            return False

        # Vertical
        regions_v = set()
        start_r = r
        while start_r >= 0 and self.grid[start_r][c] == 1:
            start_r -= 1
        start_r += 1
        
        temp_r = start_r
        while temp_r < self.size and self.grid[temp_r][c] == 1:
            regions_v.add(self.region_map[temp_r][c])
            temp_r += 1

        if len(regions_v) > 2:
            return False
            
        return True

    def check_white_line_regions_final(self):
        """REGRA 4: Validação FINAL"""
        # Horizontais
        for i in range(self.size):
            j = 0
            while j < self.size:
                if self.grid[i][j] == 1:
                    regions = set()
                    while j < self.size and self.grid[i][j] == 1:
                        regions.add(self.region_map[i][j])
                        j += 1
                    if len(regions) > 2:
                        return False
                else:
                    j += 1
        
        # Verticais
        for j in range(self.size):
            i = 0
            while i < self.size:
                if self.grid[i][j] == 1:
                    regions = set()
                    while i < self.size and self.grid[i][j] == 1:
                        regions.add(self.region_map[i][j])
                        i += 1
                    if len(regions) > 2:
                        return False
                else:
                    i += 1
        
        return True
    
    def check_white_region_isolation(self):
        """REGRA 5: Evita isolamento de brancos"""
        regions_with_whites = set(self.region_map[r][c] 
                                  for r in range(self.size) 
                                  for c in range(self.size) 
                                  if self.grid[r][c] == 1)
        
        for region_id in regions_with_whites:
            start_cell = next(((r, c) for r, c in self.regions[region_id]['cells'] if self.grid[r][c] == 1), None)
            
            if start_cell is None: continue
            
            r_start, c_start = start_cell
            queue = deque([(r_start, c_start)])
            visited = set([(r_start, c_start)])
            can_exit_region = False
            
            while queue:
                r, c = queue.popleft()

                if self.region_map[r][c] != region_id:
                    can_exit_region = True
                    continue 

                for dr, dc in [(0,1), (1,0), (0,-1), (-1,0)]:
                    nr, nc = r + dr, c + dc
                    
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        is_path = (self.grid[nr][nc] != 2)
                        
                        if is_path and (nr, nc) not in visited:
                            if self.region_map[nr][nc] != region_id:
                                can_exit_region = True
                            
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                            
            if not can_exit_region:
                return False
                
        return True
    
    def solve(self, pos=0):
        """Resolve com validações COMPLETAS e PREDITIVAS"""
        self.attempts += 1
        
        if self.attempts % 50000 == 0:
            print(f"  Tentativas: {self.attempts:,}, Backtracks: {self.backtracks:,}")
        
        if pos >= self.size * self.size:
            return (self.check_no_adjacent_blacks() and
                    self.check_white_connectivity_final() and 
                    self.check_white_line_regions_final() and
                    self.check_final_constraints())
        
        row = pos // self.size
        col = pos % self.size
        
        for value in [1, 2]:
            if not self.is_valid_placement(row, col, value):
                continue
            
            self.grid[row][col] = value
            
            region_id = self.region_map[row][col]
            if not self.check_region_constraint(region_id):
                self.grid[row][col] = 0
                continue
            
            if not self.check_white_connectivity_partial():
                self.grid[row][col] = 0
                continue
            
            if value == 1:
                if not self.check_white_line_regions_partial(row, col):
                    self.grid[row][col] = 0
                    continue
            
            if not self.check_white_region_isolation():
                self.grid[row][col] = 0
                continue
            
            if self.solve(pos + 1):
                return True
            
            self.grid[row][col] = 0
            self.backtracks += 1
        
        return False
    
    def check_final_constraints(self):
        """Valida constraints numéricas finais"""
        for region in self.regions:
            if region['constraint'] >= 0:
                black_count = sum(1 for r, c in region['cells'] if self.grid[r][c] == 2)
                if black_count != region['constraint']:
                    return False
        return True
    
    def get_border_chars(self, i, j):
        """Calcula bordas da célula"""
        region_id = self.region_map[i][j]
        top_border = (i == 0 or self.region_map[i-1][j] != region_id)
        bottom_border = (i == self.size-1 or self.region_map[i+1][j] != region_id)
        left_border = (j == 0 or self.region_map[i][j-1] != region_id)
        right_border = (j == self.size-1 or self.region_map[i][j+1] != region_id)
        return top_border, bottom_border, left_border, right_border
    
    def display(self, title="HEYAWAKE"):
        """Exibe o tabuleiro"""
        print("\n" + "="*60)
        print(f"{title} - Problema NP-Completo")
        print("="*60)
        
        print("    ", end="")
        for j in range(self.size):
            print(f"  {j} ", end="")
        print()
        
        for i in range(self.size):
            print("    ", end="")
            for j in range(self.size):
                top_border, _, left_border, right_border = self.get_border_chars(i, j)
                
                if top_border:
                    print("┌───" if left_border else "────", end="")
                    print("┐" if right_border and j == self.size - 1 else "─" if j < self.size - 1 else "┐", end="")
                else:
                    print("│   " if left_border else "    ", end="")
                    print("│" if right_border and j == self.size - 1 else " " if j < self.size - 1 else "│", end="")
            print()
            
            print(f" {i:2} ", end="")
            for j in range(self.size):
                _, _, left_border, right_border = self.get_border_chars(i, j)
                
                print("│" if left_border else " ", end="")
                
                region_id = self.region_map[i][j]
                region = self.regions[region_id]
                
                is_top_left = (i, j) == min(region['cells']) if region['cells'] else False
                constraint = region['constraint'] if is_top_left and region['constraint'] >= 0 else None
                
                cell_content = "   "
                if self.grid[i][j] == 1:
                    cell_content = " ○ "
                elif self.grid[i][j] == 2:
                    cell_content = " ■ "
                elif constraint is not None:
                    cell_content = f" {constraint} "

                print(cell_content, end="")
                print("│" if right_border else " ", end="")
            print()
        
        print("    ", end="")
        for j in range(self.size):
            _, bottom_border, left_border, right_border = self.get_border_chars(self.size-1, j)
            
            if bottom_border:
                print("└───" if left_border else "────", end="")
                print("┘" if right_border and j == self.size - 1 else "─" if j < self.size - 1 else "┘", end="")
            else:
                print("│   " if left_border else "    ", end="")
                print("│" if right_border and j == self.size - 1 else " " if j < self.size - 1 else "│", end="")
        print()
        print("="*60)
    
    def validate_solution(self):
        """Validação completa de todas as regras"""
        if not self.check_no_adjacent_blacks():
            return False, "❌ REGRA 1: Células pretas adjacentes ortogonalmente!"
        
        if not self.check_white_connectivity_final():
            return False, "❌ REGRA 2: Células brancas desconectadas!"
        
        if not self.check_final_constraints():
            return False, "❌ REGRA 3: Constraints numéricas violadas!"
        
        if not self.check_white_line_regions_final():
            return False, "❌ REGRA 4: Linha branca contínua cruza 3+ regiões!"

        if not self.check_white_region_isolation():
            return False, "❌ REGRA 5: Brancos isolados dentro de uma região!"
        
        return True, "✅ SOLUÇÃO VÁLIDA!"
    
    def auto_solve(self):
        """Resolve o puzzle"""
        print("\n🤖 INICIANDO RESOLUÇÃO...")
        print(f"📊 Tamanho: {self.size}x{self.size}")
        print(f"🔢 Regiões: {len(self.regions)}")
        
        constraints_count = sum(1 for r in self.regions if r['constraint'] >= 0)
        print(f"🎯 Constraints: {constraints_count}/{len(self.regions)} ({constraints_count/len(self.regions)*100:.1f}%)")
        
        self.display("PUZZLE INICIAL")
        
        print("\nEste programa demonstra a complexidade NP-Completo do Heyawake.")
        print("A máquina tentará resolver o puzzle usando backtracking.\n")
    
        print("✅ REGRAS OFICIAIS DO HEYAWAKE:")
        print("1. 🔴 Células PRETAS NÃO podem ser adjacentes ortogonalmente")
        print("   → Preto não toca em CIMA, BAIXO, ESQUERDA ou DIREITA")
        print("   → Diagonal pode, mas ortogonal NUNCA ❌")
        print()
        print("2. ⚪ Células BRANCAS devem estar TODAS conectadas")
        print("   → Todas as células não pintadas formam uma única componente conexa")
        print("   → Você pode caminhar de qualquer branca para qualquer outra via movimentos ortogonais")
        print()
        print("3. 🔢 Regiões com número N → EXATAMENTE N células pretas")
        print("   → Se região tem tamanho 8 e número 3 → exatamente 3 células pretas")
        print("   → Regiões sem número → qualquer quantidade (respeitando outras regras)")
        print()
        print("4. ➖ Linha branca ininterrupta NÃO pode atravessar MAIS DE 2 regiões")
        print("   → Uma linha horizontal ou vertical de células brancas consecutivas")
        print("   → Não pode cruzar mais de 2 regiões diferentes")
        
        print("\n⏱️  Resolvendo...")
        start_time = time.time()
        
        solved = self.solve()
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        if solved:
            print("✅ SOLUÇÃO ENCONTRADA!")
            self.display("SOLUÇÃO")
            
            valid, msg = self.validate_solution()
            print(f"\n🔍 Validação: {msg}")
            
            print(f"\n📈 ESTATÍSTICAS:")
            print(f"  ⏱️  Tempo: {elapsed:.3f}s")
            print(f"  🔄 Tentativas: {self.attempts:,}")
            print(f"  ⬅️  Backtracks: {self.backtracks:,}")
            if elapsed > 0:
                print(f"  📊 Taxa: {int(self.attempts/elapsed):,} tent/s")
        else:
            print("❌ NENHUMA SOLUÇÃO ENCONTRADA!")
            print(f"\n📈 Tentativas: {self.attempts:,}")
            print(f"⏱️  Tempo: {elapsed:.3f}s")
        
        print("="*60)


def main():
    print("\n" + "="*60)
    print("🎮 HEYAWAKE SOLVER - VERSÃO MELHORADA")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        size_input = input("Tamanho (4-10, Enter=6, 'q'=sair): ").strip()
        
        if size_input.lower() == 'q':
            print("👋 Até logo!")
            break
        
        size_str = ''
        for char in size_input:
            if char.isdigit():
                size_str += char
            elif size_str:
                break
        
        size = int(size_str) if size_str else 6
        size = max(4, min(10, size))
        
        print(f"\n📐 Gerando tabuleiro {size}x{size}...")
        game = HeyawakeSolver(size=size)
        game.auto_solve()
        
        continuar = input("\n🔄 Outro puzzle? (s/n): ").strip().lower()
        if continuar != 's':
            print("👋 Até logo!")
            break


if __name__ == "__main__":
    main()