Feature: No heating if door is opened

  Scenario: No heating when nothing is done
    When I do nothing
    Then event heating_on is not fired

  Scenario: No heating when I open the door
    When I send event door_opened
    Then event heating_on is not fired

  Scenario: No heating when item is placed
    Given I send event door_opened
    When I send event item_placed
    Then event heating_on is not fired

  Scenario: No heating when door is not closed
    Given I send event door_opened
    And I send event item_placed
    When I send event door_closed
    Then event heating_on is not fired

  Scenario: Allow heating if door is closed
    Given I send event door_opened
    And I send event item_placed
    And I send event door_closed
    And I send event timer_inc
    When I send event cooking_start
    Then event heating_on is fired

  Scenario: Opening door interrupts heating
    Given I reproduce "Allow heating if door is closed"
    When I send event door_opened
    Then event heating_off is fired