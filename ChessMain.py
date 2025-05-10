import pygame as p
import ChessEngine, ChessAIMinimax, ChessAINegamax
import sys
from multiprocessing import Process, Queue
import time

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))

def drawDifficultySelectionScreen(screen):
    screen.fill(p.Color("white"))
    font = p.font.SysFont("Arial", 30, True)

    title = font.render("SELECT DIFFICULTY", True, p.Color("black"))
    screen.blit(title, (BOARD_WIDTH // 2 - title.get_width() //2, 50))

    easy_button = p.Rect(BOARD_WIDTH // 2 - 150, 150 , 300, 50)
    medium_button = p.Rect(BOARD_WIDTH // 2 - 150, 250 , 300, 50)
    hard_button = p.Rect(BOARD_WIDTH // 2 - 150, 350 , 300, 50)

    p.draw.rect(screen, p.Color("black"), easy_button, border_radius=5)
    p.draw.rect(screen, p.Color("black"), medium_button, border_radius=5)
    p.draw.rect(screen, p.Color("black"), hard_button, border_radius=5)

    easy_text = font.render("EASY (DEPTH: 2)", True, p.Color("white"))
    medium_text = font.render("MEDIUM (DEPTH: 3)", True, p.Color("white"))
    hard_text = font.render("HARD (DEPTH: 4)", True, p.Color("white"))

    screen.blit(easy_text, easy_text.get_rect(center=easy_button.center))
    screen.blit(medium_text, medium_text.get_rect(center=medium_button.center))
    screen.blit(hard_text, hard_text.get_rect(center=hard_button.center))

    return easy_button, medium_button, hard_button

def drawSimulationButtons(screen):
    button_font = p.font.SysFont("Arial", 20, True)
    
    # Simulation button
    sim_button_rect = p.Rect(BOARD_WIDTH + 10, BOARD_HEIGHT - 100, 230, 40)
    p.draw.rect(screen, p.Color("blue"), sim_button_rect, border_radius=5)
    sim_button_text = button_font.render("Simulation", True, p.Color("white"))
    screen.blit(sim_button_text, sim_button_text.get_rect(center=sim_button_rect.center))
    
    # Back to Real button
    back_button_rect = p.Rect(BOARD_WIDTH + 10, BOARD_HEIGHT - 50, 230, 40)
    p.draw.rect(screen, p.Color("red"), back_button_rect, border_radius=5)
    back_button_text = button_font.render("Back to Real", True, p.Color("white"))
    screen.blit(back_button_text, back_button_text.get_rect(center=back_button_rect.center))
    
    return sim_button_rect, back_button_rect

def drawAlgorithmSelectionScreen(screen):
    font = p.font.SysFont("Arial", 30, True)
    text = font.render("SELECT ALGORITHM", True, p.Color("black"))
    screen.blit(text, (BOARD_WIDTH // 2 - text.get_width() // 2, 50))
    
    minmax_button_rect = p.Rect(BOARD_WIDTH // 2 - 150, 150, 300, 50)
    p.draw.rect(screen, p.Color("black"), minmax_button_rect, border_radius=5)
    minmax_button_text = font.render("Minimax", True, p.Color("white"))
    screen.blit(minmax_button_text, minmax_button_text.get_rect(center=minmax_button_rect.center))
    
    negamax_button_rect = p.Rect(BOARD_WIDTH // 2 - 150, 250, 300, 50)
    p.draw.rect(screen, p.Color("black"), negamax_button_rect, border_radius=5)
    negamax_button_text = font.render("Negamax", True, p.Color("white"))
    screen.blit(negamax_button_text, negamax_button_text.get_rect(center=negamax_button_rect.center))
    
    return minmax_button_rect, negamax_button_rect

def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    
    algorithm = None
    while algorithm is None:
        minmax_button_rect, negamax_button_rect = drawAlgorithmSelectionScreen(screen)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                pos = p.mouse.get_pos()
                if minmax_button_rect.collidepoint(pos):
                    algorithm = "Minimax"
                elif negamax_button_rect.collidepoint(pos):
                    algorithm = "Negamax"
        p.display.flip()
    
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False
    animate = False
    loadImages()
    
    difficulty = None
    _depth = None
    while difficulty is None: 
        easy_button, medium_button, hard_button = drawDifficultySelectionScreen(screen)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            elif e.type == p.MOUSEBUTTONDOWN:
                pos = p.mouse.get_pos()
                if easy_button.collidepoint(pos):
                    difficulty = "EASY"
                    _depth = 2
                    print("Selected EASY")
                elif medium_button.collidepoint(pos):
                    difficulty = "MEDIUM"
                    _depth = 3
                    print("Selected MEDIUM")
                elif hard_button.collidepoint(pos):
                    difficulty = "HARD"
                    _depth = 4
                    print("Selected HARD")
        p.display.flip()
    
    running = True
    square_selected = ()
    player_clicks = []
    game_over = False
    ai_thinking = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    player_one = True
    player_two = False
    
    simulation_mode = False
    simulation_moves = []
    saved_state = None
    simulation_move_count = 0
    
    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()

            elif e.type == p.MOUSEBUTTONDOWN:
                pos = p.mouse.get_pos()

                sim_button_rect, back_button_rect = drawSimulationButtons(screen)

                if sim_button_rect.collidepoint(pos):
                    if not simulation_mode:
                        simulation_mode = True
                        saved_state = game_state.copy()
                        simulation_moves = []
                        simulation_move_count = 0

                if back_button_rect.collidepoint(pos):
                    if simulation_mode:
                        simulation_mode = False
                        game_state = saved_state  # Reset to the saved state
                        saved_state = None
                        simulation_moves = []  # Clear the simulation moves
                        simulation_move_count = 0
                        valid_moves = game_state.getValidMoves()

                if not game_over and not simulation_mode:
                    col = pos[0] // SQUARE_SIZE
                    row = pos[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)
                    if len(player_clicks) == 2 and human_turn:
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                if e.key == p.K_r:
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False

        if simulation_mode and not game_over:
            if len(simulation_moves) == 0:
                simulation_state = game_state.copy()
                simulation_moves = [(simulation_state, None)]

            current_simulation_state, last_move = simulation_moves[-1]
            valid_moves = current_simulation_state.getValidMoves()

            if simulation_move_count < 5:
                return_queue = Queue()
                if algorithm == "Minimax":
                    ChessAIMinimax.findBestMove(current_simulation_state, valid_moves, return_queue, _depth)
                else:
                    ChessAINegamax.findBestMove(current_simulation_state, valid_moves, return_queue, _depth)

                ai_move = return_queue.get()
                if ai_move:
                    animateSimulationMove(ai_move, screen, current_simulation_state.board, clock, [p.Color("white"), p.Color("gray")], SQUARE_SIZE, IMAGES)
                    new_simulation_state = current_simulation_state.copy()
                    new_simulation_state.makeMove(ai_move)
                    simulation_moves.append((new_simulation_state, ai_move))
                    simulation_move_count += 1
                    time.sleep(1)


            # Hiển thị trạng thái mô phỏng
            drawGameState(screen, simulation_moves[-1][0], valid_moves, square_selected)

            # Highlight tất cả các nước đi trong chế độ simulation
            highlightSquaresInSimulation(screen, simulation_moves)
            drawSimulationButtons(screen)

        elif not simulation_mode and not game_over and not human_turn:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()
                if algorithm == "Minimax":
                    move_finder_process = Process(target=ChessAIMinimax.findBestMove, args=(game_state, valid_moves, return_queue, _depth))
                else:
                    move_finder_process = Process(target=ChessAINegamax.findBestMove, args=(game_state, valid_moves, return_queue, _depth))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = ChessAIMinimax.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                colors = [p.Color("white"), p.Color("gray")]
                animateMove(game_state.move_log[-1], screen, game_state.board, clock, colors)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False

        drawGameState(screen, game_state if not simulation_mode else simulation_moves[-1][0], valid_moves, square_selected)
        # drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            drawEndGameText(screen, "Black wins by checkmate" if game_state .white_to_move else "White wins by checkmate")
        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        sim_button_rect, back_button_rect = drawSimulationButtons(screen)

        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, game_state, valid_moves, square_selected, simulation_moves=None):
    drawBoard(screen)
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)
    
    if simulation_moves:  # If in simulation mode, highlight simulation moves
        highlightSquaresInSimulation(screen, simulation_moves)

def drawBoard(screen):
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = colors[(row + col) % 2]
            p.draw.rect(screen, color, p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def highlightSquares(screen, game_state, valid_moves, square_selected):
    if len(game_state.move_log) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color("green"))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == ("w" if game_state.white_to_move else "b"):
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("blue"))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            s.fill(p.Color("yellow"))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

def highlightSquaresInSimulation(screen, moves):
    s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
    s.set_alpha(100)  # Transparency
    s.fill(p.Color("orange"))  # Highlight color for simulation moves
    for simulation_state, move in moves:
        if move:
            screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))



        
def drawPieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# def drawMoveLog(screen, game_state, font):
#     move_log = game_state.move_log
#     move_texts = [font.render(move.getChessNotation(), True, p.Color("black")) for move in move_log]
#     for i, text in enumerate(move_texts):
#         screen.blit(text, p.Rect(MOVE_LOG_PANEL_WIDTH - 200, MOVE_LOG_PANEL_HEIGHT - (i * 20) - 20, 200, 20))

def drawEndGameText(screen, text):
    font = p.font.SysFont("Arial", 40, True)
    text_obj = font.render(text, True, p.Color("red"))
    screen.blit(text_obj, (BOARD_WIDTH // 2 - text_obj.get_width() // 2, BOARD_HEIGHT // 2))


def animateMove(move, screen, board, clock, colors):
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frames_per_square = 10
    frame_count = (abs(dR) + abs(dC)) * frames_per_square
    for frame in range(frame_count + 1):
        r, c = (move.start_row + dR * frame / frame_count, move.start_col + dC * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        if move.piece_captured != "--":
            screen.blit(IMAGES[move.piece_captured], end_square)
        screen.blit(IMAGES[move.piece_moved],
                    p.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)
        
def animateSimulationMove(move, screen, board, clock, colors, SQUARE_SIZE, IMAGES):
    # Calculate change in rows and columns
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    
    # Frames per square and total frame count based on the movement
    frames_per_square = 10
    frame_count = (abs(dR) + abs(dC)) * frames_per_square
    
    # Loop through frames to animate the move
    for frame in range(frame_count + 1):
        # Calculate intermediate position of the piece for smooth movement
        r = move.start_row + dR * frame / frame_count
        c = move.start_col + dC * frame / frame_count
        
        # Clear the screen and draw the board and pieces
        screen.fill(p.Color(0, 0, 0))  # Clear the screen with black
        drawBoard(screen)  # Function to draw the chessboard
        drawPieces(screen, board)  # Function to draw the pieces on the board
        
        # Highlight the end square (optional)
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)  # Highlight the destination square
        
        # If a piece is captured, display the captured piece on the end square
        if move.piece_captured != "--":
            screen.blit(IMAGES[move.piece_captured], end_square)
        
        # Draw the moving piece at its intermediate position
        moving_piece_rect = p.Rect(c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        screen.blit(IMAGES[move.piece_moved], moving_piece_rect)
        
        # Refresh the display and control the frame rate
        p.display.flip()
        clock.tick(60)  # 60 frames per second

if __name__ == "__main__":
    main()