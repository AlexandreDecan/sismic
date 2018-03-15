Feature: Elevator

  Scenario: Elevator starts on ground floor
    When I do nothing
    Then variable current equals 0
    And variable destination equals 0

  Scenario: Elevator can move to 7th floor
    When I send event floorSelected with floor=7
    Then variable current equals 7

  Scenario: Elevator can move to 4th floor
    When I send event floorSelected
      | parameter  | value |
      | floor      | 4     |
      | dummy      | None  |
    Then variable current equals 4

  Scenario: Elevator reaches ground floor after 10 seconds
    When I reproduce "Elevator can move to 7th floor"
    Then variable current equals 7
    When I wait 10 seconds
    Then variable current equals 0
    # Example using another step:
    And expression "current == 0" holds

  Scenario Outline: Elevator can reach floor from 0 to 5
    When I send event floorSelected with floor=<floor>
    Then variable current equals <floor>

    Examples:
      | floor |
      | 0     |
      | 1     |
      | 2     |
      | 3     |
      | 4     |
      | 5     |
