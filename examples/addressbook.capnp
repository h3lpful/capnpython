@0x934efea7f017fff0;

const qux :UInt32 = 123;


struct Person {
  id @0 :UInt32;
  name @1 :Text;
  email @2 :Text;
  phones @3 :List(PhoneNumber);

  struct PhoneNumber {
    number @0 :Text;
    type @1 :Type;

    enum Type {
      mobile @0;
      home @1;
      work @2;
    }
  }
  employment :union {
    unemployed @4 :Void;
    employer @5 :Text;
    school @6 :Text;
    selfEmployed @7 :Void;
    # We assume that a person is only one of these.
  }

  testGroup :group {
    field1 @8 :UInt32;
    field2 @9 :UInt32;
    field3 @10 :UInt32;
  }
  extraData @11 :Data;
}

struct AddressBook {
  people @0 :List(Person);
}

