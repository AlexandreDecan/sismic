Feature: Cooking

  Scenario: Start cooking food
    Given I open the door
    And I place an item in the oven
    And I close the door
    And I press increase timer button 5 times
    And I press increase power button
    When I press start button
    Then heating turns on

  Scenario: Stop cooking food
    Given I reproduce "Start cooking food"
    When 2 seconds elapsed
    Then variable timer equals 3
    When I press stop button
    Then variable timer equals 0
    And heating turns off

  Scenario: Cooking stops after preset time
    Given I reproduce "Start cooking food"
    When 5 seconds elapsed
    Then variable timer equals 0
    And heating turns off


