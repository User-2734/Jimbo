# selenium imports for playing the game
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

# other packages
import random
from main import Connect4
from time import sleep
from bs4 import BeautifulSoup

def wait() -> None:
    """Waits a random amount of time. Used to avoid bot detection"""
    sleep(random.uniform(0, 3))

def parse_circle(circle_classes: list[str]) -> int | None:
    """Takes in the circle's classes and determines what player it belongs to
    
    Args:
        circle_classes: a list of the classes of a circle
    
    Returns:
        an int representing the player that the piece belongs to, 0 if the peice is an empty slot
        or None if none of the above"""
    if 'circle-dark' in circle_classes: return -1
    if 'circle-light' in circle_classes: return 1
    if 'empty-slot' in circle_classes: return 0
    return None

class TerminalGameException(Exception): pass # exception for when a game is in a terminal state
class AbortedGameException(Exception): pass  # For when the game is quit prematurily

class Bot():
    def __init__(self) -> None:
        # we are named Jimbo
        self.name = 'Jimbo'

        # load uBlock into the bot to prevent ad fraud
        self.options = webdriver.ChromeOptions()
        self.options.add_extension('uBlock-Origin.crx')

        # create a selenium web driver to interact with the website
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get("https://papergames.io/en/connect4")

    def get_element(self, selector: str) -> WebElement:
        """Retreive a given element using the webdriver
        
        Args:
            selector: the css selector to the element
        
        Returns:
            the element we found
        """
        return WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    
    def click_button_by_text(self, text: str) -> WebElement:
        """Retreive a given element using the webdriver
        
        Args:
            selector: the css selector to the element
        
        Returns:
            the found element
        """
        return WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.XPATH, f"//*[text()=\"{text}\"]/ancestor::button")))
    
    def click_button(self, selector: str, delay=True) -> None:
        """Click a button
        
        Args:
            selector: the css selector of the element to click
            delay: whether or not to add in a random delay (helps avoid bot detection)
        """
        button = self.get_element(selector)
        if delay: wait()
        button.click()
        return
    
    def input_name(self, selector: str, delay=True) -> None:
        """Types self.name into a selected text input
        
        Args:
            selector: the css selector for the name feild
            delay: whether to add in random delay (helps avoid bot detection)"""
        if self.driver.current_url != 'https://papergames.io/en/connect4': return
        feild = self.get_element(selector)
        if delay: wait()
        feild.send_keys(self.name)
        return

    def get_game_state(self) -> Connect4:
        """Gets the game's state from the website and parses it into a connect 4 board
        
        Returns:
            The state of the board on the website"""
        # click to prevent extranious floating pieces
        body = self.get_element('body')
        body.click()

        # grab the board and extract the circles in it
        element = self.get_element('#connect4')
        html = element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        circles = soup.find_all('circle')

        # determine which player occupies what square
        circles = [e['class'] for e in circles]
        circles = map(parse_circle, circles)
        circles = [circle for circle in circles if circle is not None]

        # convert the list of circles into a state that can be used
        board = [[] for _ in range(7)]
        for i, player in enumerate(circles):
            board[i % 7].append(player)
        
        # pack it up into a connect 4 board
        c = Connect4()
        c.state = board
        return c

    def determine_side(self) -> str:
        """Determines if our score is on the left or right side of the scoreboard
        
        Returns:
            'r' or 'l' if we're on the left or right respectivley
        """
        # figure out if we're on the left or the right
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Find all spans with the player name
        player_name_spans = soup.find_all('span', class_='text-truncate cursor-pointer')
        
        # Extract and print the text content (names)
        left, right = [span.get_text(strip=True) for span in player_name_spans]

        if right == self.name:
            return 'r'
        elif left == self.name:
            return 'l'
        raise Exception('Could not find name')
        
    def player(self) -> int:
        """Determines what color we're playing as
        
        Returns:
            1 or -1 depending on the color"""
        side = self.determine_side()

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Find all spans with the player name
        circles = soup.find_all('circle', class_='shape')
        if side == 'l':
            return parse_circle(circles[0]['class'])
        if side == 'r':
            return parse_circle(circles[1]['class'])
    
    def is_turn(self) -> bool:
        """checks if it's our turn
        
        Returns:
            True if it's our turn, else False"""
        side = self.determine_side()
        if side == 'l':
            index = 0
        if side == 'r':
            index = 1
        
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Find all avatars
        avatars = soup.find_all('app-user-avatar', class_='ng-star-inserted')

        # check for a loading ring
        rings = [avatar.find('circle') is not None for avatar in avatars]
        return rings[index]
    
    def wait_for_turn(self) -> None:
        """Waits for our turn by watching for a green circle around our name.
        Throws:
            TerminalGameException: The other player has won, so we will not get a turn
            AbortedGameException: The other player has aborted the game"""
        while not self.is_turn():
            if self.get_game_state().is_terminal():
                raise TerminalGameException()
            if self.driver.current_url == 'https://papergames.io/en/connect4':
                raise AbortedGameException()
            sleep(0.1)

    def find_game(self) -> None:
        """Gets us into an online game"""
        self.click_button('body > app-root > app-navigation > div > div.d-flex.flex-column.h-100.w-100 > main > app-game-landing > div > div > div > div.col-12.col-lg-9.dashboard > div.card.area-buttons.d-flex.justify-content-center.align-items-center.flex-column > button.btn.btn-secondary.btn-lg.d-flex.justify-content-start.align-items-start.flex-column')
        # TODO: detect if the website actually prompts us for a name
        self.input_name('#mat-mdc-dialog-0 > div > div > app-guest-registration-dialog > form > app-dialog-layout > div > section > div > div > input')
        self.click_button('#mat-mdc-dialog-0 > div > div > app-guest-registration-dialog > form > app-dialog-layout > div > footer > button')
    
    def has_first_turn(self) -> bool:
        """Checks if we have to play the first move
        
        Returns:
            true if we have the first move, else false"""
        empty_state = Connect4()
        return self.get_game_state() == empty_state
    
    def get_board_moves(self) -> list[WebElement]:
        """Gets the elements we click to make moves
        
        Returns:
            A list of clickable web elements"""
        move_template = "#connect4 > div > div.grid-item.cell-1-{x}.selectable.ng-star-inserted"
        move_selectors = [move_template.format(x=i + 1) for i in range(7)]
        move_buttons = [self.get_element(selector) for selector in move_selectors]
        return move_buttons

    def play_round(self) -> None:
        """Plays a single game of connect 4 online"""
        # wait for the board to move in
        try:
            move_buttons = self.get_board_moves()
        except TimeoutException:
            if self.driver.current_url == 'https://papergames.io/en/connect4':
                raise AbortedGameException()

        # determine what player we are
        player = self.player()

        while True:
            # wait for our turn
            try:
                self.wait_for_turn()
            except TerminalGameException:
                break

            # get the state of the board
            state = self.get_game_state()
            state.player = player
            # show the board for debugging purposes (it also looks cool)
            state.show()
            print(f"Player: {state.player_to_string(state.player)}")
            # stop playing if the state is terminal
            if state.is_terminal(): break
            
            if self.has_first_turn():
                move = 3 # always play the middle on the first turn
            else:
                # calculate the best move
                move = state.best_move()
            
            print(f"Move: {move}")
            # input the move into the website
            move_buttons[move].click()
            # check if we've won
            state.make_move(move)
            if state.is_terminal(): break
            sleep(1)
            wait()

    def play(self) -> None:
        """Plays a round online"""
        # TODO: add in support for multiple consecutive games
        self.find_game()
    
        print("Waiting for round...")
        try:
            self.play_round()
        except AbortedGameException:
            pass
        print('Game Over')

if __name__ == '__main__':
   b = Bot()
   b.play()
