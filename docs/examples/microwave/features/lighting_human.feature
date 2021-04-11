Feature: Lighting

  @fixture.sismic_application
  Scenario: Lamp is on when door is open
    When I open the door
    Then lamp turns on

  @fixture.sismic_application
  Scenario: Lamp is off when door is closed
    Given I reproduce "Lamp is on when door is open"
    When I close the door
    Then lamp turns off

  @fixture.sismic_application
  Scenario: Lamp is on while cooking
    Given I open the door
    And I place an item in the oven
    And I close the door
    And I press increase timer button 5 times
    When I press start button
    Then lamp turns on

  @fixture.sismic_application
  Scenario: Lamp turns off after cooking
    Given I reproduce "Lamp is on while cooking"
    When I press stop button
    Then lamp turns off

