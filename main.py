from random import shuffle

class InvalidMoveError(Exception): pass # raised when someone makes an invalid move
        
class Connect4:
    """A 7 wide by 6 tall connect 4 board

    Attributes:
        player: An integer representing the player. Should always be either 1 or -1
        state: the state of the board. each sub array represents a column
    """
    def __init__(self) -> None:
        """Initializes the instance"""
        self.player = 1 # player 1 goes first
        # create a 7 wide by 6 tall board, rotated 90 degrees
        self.state = [[0] * 6 for _ in range(7)]

    def __hash__(self) -> int:
        """Returns a hash value of the state"""
        return hash((self.player, tuple(tuple(column) for column in self.state)))
    
    def __eq__(self, other) -> bool:
        """Checks if this board is the same as another board. It ignores the active player"""
        return self.state == other.state

    def make_move(self, move: int) -> None:
        """Drops a piece into the board.
        
        Args:
            move: an integer representing which column to drop the piece, starting at 0"""
        self.validate_move(move)

        # figure out the next free space
        index = 0
        while self.state[move][index] == 0:
            index += 1
            if index == 6: break
        index -= 1

        # make the move
        self.state[move][index] = self.player

        # switch players for next turn
        self.player *= -1
        return
    
    def validate_move(self, move: int) -> None:
        """Raises an exception if the move is invalid
        
        Args:
            move: the move to validate in the range [0, 6]
        """
        if not self.is_valid_move(move): raise Exception('Invalid Move')
        return
    
    def is_valid_move(self, move: int) -> bool:
        """Checks if a move is valid
        
        Args:
            move: the move to check in the range [0, 6]
        
        Returns:
            True if the move is valid else False"""
        return move in self.valid_moves()
    
    def valid_moves(self) -> list[int]:
        """Gets all the valid moves
        
        Returns:
            A list of all the valid moves that can be made in the current state"""
        return [column for column in range(7) if self.has_space(column)]
    
    def has_space(self, column: int) -> bool:
        """Checks if a column has space for more pieces
        
        Args:
            column: the index of the column to check
        
        Returns:
            True if the column can accept more pieces else false"""
        return self.state[column][0] == 0
    
    def column_full(self, column: int) -> bool:
        """checks if a column is full
        
        Args:
            column: the column to check
        
        Returns:
            True if the column is full else False"""
        # move validation is done inside of self.has_space
        return not self.has_space(column)
    
    def is_winner(self, player: int) -> bool:
        """check if a player wins
        
        Args:
            player: the player to check. Should be -1 or 1
        
        Returns:
            True if the player is a winner, else False"""
        return self.count_groups(player, 4) > 0
    
    def count_groups(self, player: int, size: int) -> int:
        """Iterates over every 4 piece line in the game, and checks if it has
        more than size pieces belonging to the specified player
        
        Args:
            player: the player to check
            size: the number of pieces in the group to match or exceed. Should not be more than 4
        
        Returns:
            The number of valid groups found
            """
        ROWS = len(self.state[0])  # Number of rows (from column height)
        COLS = len(self.state)     # Number of columns

        count = 0

        # Check verticals
        for col in range(COLS):
            for row in range(ROWS - 3):
                if [self.state[col][row + i] for i in range(4)].count(player) >= size:
                    count += 1

        # Check horizontals
        for col in range(COLS - 3):
            for row in range(ROWS):
                if [self.state[col + i][row] for i in range(4)].count(player) >= size:
                    count += 1

        # Check diagonals (bottom-left to top-right)
        for col in range(COLS - 3):
            for row in range(ROWS - 3):
                if [self.state[col + i][row + i] for i in range(4)].count(player) >= size:
                    count += 1

        # Check diagonals (top-left to bottom-right)
        for col in range(COLS - 3):
            for row in range(3, ROWS):
                if [self.state[col + i][row - i] for i in range(4)].count(player) >= size:
                    count += 1

        return count
    
    def score(self) -> int:
        """Figure out if we have a winner
        
        Returns:
            the final score of the board."""

        if self.is_winner(1):
            return 1
        if self.is_winner(-1):
            return -1
        return 0
    
    def has_winner(self) -> bool:
        """Checks if someone has won the game
        
        Returns:
            True if someone one, else False"""
        return self.score() != 0
    
    def is_terminal(self) -> bool:
        """Checks if the board is in a terminal state (ie someone won or the board is full)
        
        Returns:
            True if the board is terminal, else False"""
        return self.has_winner() or all(self.column_full(i) for i in range(7))
    
    def clone(self) -> 'Connect4':
        """Make a copy of ourself
        
        Returns:
            A copy of the current board"""
        clone = Connect4()
        clone.state = [column[:] for column in self.state]
        clone.player = self.player
        return clone
    
    def children(self) -> list['Connect4']:
        """Generates all boards that can result from making a move
        
        Returns:
            A list of boards that can be made by making a move"""
        moves = self.valid_moves()
        children = [self.clone() for _ in moves]
        for index, child in enumerate(children):
            child.make_move(moves[index])
        return children
    
    def temp_score(self, start_player: int) -> int:
        """Returns the heuristic value of a board based off the number of almost complete 4s
        
        Args:
            start_player: the player that is making a move on the root board
        
        Returns:
            The number of possible connect 4s that have at least 3 pieces
        """
        return self.count_groups(start_player, 3) * start_player
    
    def score_state(self, depth: int, states: dict, alpha: int, beta: int, start_player: int) -> int:
        """Uses minimax to determine the score of the state
        
        Args:
            depth: the max recursion depth
            states: a dictionary of all previously explored nodes and their scores
            alpha: the alpha value for alpha beta pruning
            beta: the beta value for alpha beta pruning
            start_player: the player making a move on the root board
        
        Returns:
            The score of the board found via minimax"""

        if self in states: return states[self]
        if self.is_terminal(): 
            # prolong the inevitable for as long as possible
            return (self.score() * 100) - (start_player * depth) # base case
        if depth == 0:
            return self.temp_score(start_player) # TODO make this score the intrensic value

        scores = []
        if self.player == 1:
            for child in self.children():
                score = child.score_state(depth - 1, states, alpha, beta, start_player)
                scores.append(score)

                alpha = max(score, alpha)
                if alpha >= beta: break
        if self.player == -1:
            for child in self.children():
                score = child.score_state(depth - 1, states, alpha, beta, start_player)
                scores.append(score)  

                beta = min(score, beta)
                if alpha >= beta: break

        score = 0
        if self.player == 1:
            score = max(scores)
        if self.player == -1:
            score = min(scores)
        
        states[self] = score
        return score
    
    def best_move(self, recursion_depth=6) -> int:
        """Use minimax to find the best move
        
        Args:
            recursion_depth: the depth to recurse to
        
        Returns:
            The best move found from minimax"""
        # get all the possible moves
        moves = self.valid_moves()
        children = self.children()
        states = {}
        # calculate all the scores
        scores = [child.score_state(recursion_depth, states, float('-inf'), float('inf'), self.player) for child in children]
        
        # randomize the order in which we evaluate moves to decrease predictability
        indices = list(range(len(moves)))
        shuffle(indices)
        # find the best move
        best_index = 0
        if self.player == 1:
            best_index = max(indices, key=lambda x: scores[x])
        if self.player == -1:
            best_index = min(indices, key=lambda x: scores[x])
        
        # return the best move
        return moves[best_index]
    
    def player_to_string(self, player: int) -> str:
        """Converts a player in range [-1, 1] to a string for display purposes
        
        Args:
            player: the player to convert
        
        Returns:
            a string containing the character to display"""
        player += 1
        return 'X O'[player]

    def show(self):
        """Print out the board for debugging/playing in the terminal"""
        for row in range(6):  # From top to bottom
            print(' '.join(str(self.player_to_string(self.state[col][row])) for col in range(7)))
        print('0 1 2 3 4 5 6')  # Column indices
 
if __name__ == '__main__':
    # create a board
    c = Connect4()
    # continue while the game is running
    while not c.is_terminal():
        c.show()
        if c.player == 1:
            # TODO: add in input validation
            c.make_move(int(input('Your Move: ')))
        elif c.player == -1:
            # get the computer's move
            move = c.best_move()
            c.make_move(move)
            print(f"Computer Move: {move}")