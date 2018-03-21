Feature: Cook food

  Scenario: Cook food
    Given I open the door
    And I place an item in the oven
    And I close the door
    And I press increase timer button 5 times
    And I press increase power button
    When I press start button
    Then heating turns on

  Scenario: No heating when door is not closed
    Given I reproduce "Cook food"
    And I open the door
    When I press start button
    Then heating does not turn on

  Scenario: Opening door interrupts heating
    Given I reproduce "Cook food"
    And 3 seconds elapsed
    When I open the door
    Then heating turns off

  Scenario: Lamp is on when door is open
    When I open the door
    Then lamp turns on
    When I close the door
    Then lamp turns off

  Scenario: Lamp is on while cooking
    When I reproduce "Cook food"
    Then lamp turns on

  Scenario: Cooking can be stopped stop
    Given I reproduce "Cook food"
    When 2 seconds elapsed
    Then variable timer equals 3
    When I press stop button
    Then variable timer equals 0
    And heating turns off

