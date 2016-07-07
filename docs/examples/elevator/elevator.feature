Feature: Elevator

  Scenario: Elevator starts on ground floor
    Then the value of current should be 0
    And the value of destination should be 0

  Scenario: Elevator can move to 7th floor
    When I send event floorSelected with floor=7
    Then the value of current should be 7

  Scenario: Elevator can move to 4th floor
    When I send event floorSelected
      | parameter  | value |
      | floor      | 4     |
      | dummy      | None  |
    Then the value of current should be 4

  Scenario: Elevator reaches ground floor after 10 seconds
    Given I reproduce "Elevator can move to 7th floor"
    When I wait 10 seconds
    Then the value of current should be 0
    # Notice the variant using "holds":
    And expression current == 0 should hold

  Scenario Outline: Elevator can reach floor from 0 to 5
    When I send event floorSelected with floor=<floor>
    Then the value of current should be <floor>

    Examples:
      | floor |
      | 0     |
      | 1     |
      | 2     |
      | 3     |
      | 4     |
      | 5     |
