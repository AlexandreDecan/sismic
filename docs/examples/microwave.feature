Feature: microwave

  Scenario: Microwave startup configuration
    Then state heating.off should be active
    And state lamp.off should be active
    And state turntable.off should be active
    And state door.close should be active

  Scenario: Microwave starts
    Given I send event incDuration
    When I send event startstop
    Then state heating.on should be active

  Scenario: Microwave stops when the door is open
    Given I reproduce "Microwave starts"
    And I wait 1 second 3 times
    When I send event toggledoor
    Then state heating.on should not be active

  Scenario: Microwave does not start if door is open
    Given I send event toggledoor
    And I send event incDuration
    Then state door.open should be active
    When I send event startstop
    Then state heating.on should not be active

  Scenario: Microwave bells when it stops heating
    Given I reproduce "Microwave starts"
    When I wait 1 second 5 times
    Then event ding should be fired