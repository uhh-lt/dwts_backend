from app.util.singleton_meta import SingletonMeta


def test_always_same_instance_simple():
    class MySingleton(metaclass=SingletonMeta):
        def __init__(self):
            print("In init")

    first = MySingleton()
    second = MySingleton()

    assert first is second
    # noinspection PyUnresolvedReferences
    assert first._SingletonMeta__singleton is second._SingletonMeta__singleton


def test_always_same_instance_with_parameter():
    class MySingleton(metaclass=SingletonMeta):
        def __init__(self, x):
            self.x = x
            print(f"x is {x}")

    first = MySingleton(x=123)
    second = MySingleton(x=456)

    assert first is second
    assert first.x == second.x
    # noinspection PyUnresolvedReferences
    assert first._SingletonMeta__singleton is second._SingletonMeta__singleton


def test_always_same_instance_with_new():
    class MySingleton(metaclass=SingletonMeta):
        def __new__(cls, *args, **kwargs):
            cls.my_class_var = "my class variable"
            return super(MySingleton, cls).__new__(cls)

    first = MySingleton()
    second = MySingleton()

    assert first is second
    assert first.my_class_var == second.my_class_var

    # noinspection PyUnresolvedReferences
    assert first._SingletonMeta__singleton is second._SingletonMeta__singleton
