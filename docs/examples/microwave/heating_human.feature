# Run with sismic-behave microwave.yaml --features heating_human.feature --steps heating_steps.py 

Feature: No heating if door is opened

  Scenario: No heating when nothing is done
    When I power up the microwave
    Then heating should not be on

  Scenario: No heating when I open the door
    When I open the door
    Then heating should not turn on

  Scenario: No heating when item is placed
    Given I open the door
    When I place an item
    Then heating should not turn on

  Scenario: No heating when door is not closed
    Given I open the door
    And I place an item
    When I close the door
    Then heating should not turn on

  Scenario: Allow heating if door is closed
    Given I open the door
    And I place an item
    And I close the door
    And I increase the cooking duration
    When I press the start button
    Then heating should turn on

  Scenario: Opening door interrupts heating
    Given I reproduce "Allow heating if door is closed"
    When I open the door
    Then heating should turn off