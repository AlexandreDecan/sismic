Feature: No heating if door is opened

  Scenario: No heating when nothing is done
    Given I do nothing
    And I execute the statechart
    Then event heating_on should not be fired

  Scenario: No heating when I open the door
    When I send event door_opened
    Then event heating_on should not be fired

  Scenario: No heating when item is placed
    Given I send event door_opened
    When I send event item_placed
    Then event heating_on should not be fired

  Scenario: No heating when door is not closed
    Given I send event door_opened
    And I send event item_placed
    When I send event door_closed
    Then event heating_on should not be fired    

  Scenario: Allow heating if door is closed
    Given I send event door_opened
    And I send event item_placed
    And I send event door_closed
    And I send event input_timer_inc
    When I send event input_cooking_start
    Then event heating_on should be fired

  Scenario: Opening door interrupts heating
    Given I reproduce "Allow heating if door is closed"
    When I send event door_opened
    Then event heating_off should be fired