pragma solidity ^0.8.0;

contract PaymentContract {
    address payable public owner;
    address payable public customer;
    address payable public courier;
    uint256 public amount;
    bool public paid;
    bool public courierAssigned;

    constructor(
        address payable _owner,
        address payable _customer,
        uint256 _amount
    ) {
        owner = _owner;
        customer = _customer;
        amount = _amount;
        paid = false;
        courierAssigned = false;
    }

    function pay() external payable {
        require(msg.sender == customer, "Only customer can pay");
        require(msg.value == amount, "Incorrect amount");
        require(!paid, "Already paid");
        paid = true;
    }

    function assignCourier(address payable _courier) external {
        require(msg.sender == owner, "Only owner can assign courier");
        require(!courierAssigned, "Courier already assigned");
        courier = _courier;
        courierAssigned = true;
    }

    function finalize() external {
        require(msg.sender == owner, "Only owner can finalize");
        require(paid, "Payment not complete");
        require(courierAssigned, "Courier not assigned");

        uint256 ownerAmount = (amount * 80) / 100;
        uint256 courierAmount = amount - ownerAmount;

        owner.transfer(ownerAmount);
        courier.transfer(courierAmount);
    }

    function isPaid() external view returns (bool) {
        return paid;
    }
}