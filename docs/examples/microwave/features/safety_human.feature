Feature: Safety criterion

  Background: Start cooking food
    Given I open the door
    And I place an item in the oven
    And I close the door
    And I press increase timer button 5 times

  Scenario: NO cooking when door is not closed
    Given I open the door
    When I press start button
    Then heating does not turn on

  Scenario: Opening door interrupts cooking
    Given I press start button
    And 3 seconds elapsed
    When I open the door
    Then heating turns off
