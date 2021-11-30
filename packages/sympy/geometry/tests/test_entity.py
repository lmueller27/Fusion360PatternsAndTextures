from sympy import Symbol, Rational, S
from sympy.geometry import Circle, Ellipse, Line, Point, Polygon, Ray, RegularPolygon, Segment, Triangle
from sympy.geometry.entity import scale, GeometryEntity
from sympy.testing.pytest import raises

from random import random


def test_entity():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)

    assert GeometryEntity(x, y) in GeometryEntity(x, y)
    raises(NotImplementedError, lambda: Point(0, 0) in GeometryEntity(x, y))

    assert GeometryEntity(x, y) == GeometryEntity(x, y)
    assert GeometryEntity(x, y).equals(GeometryEntity(x, y))

    c = Circle((0, 0), 5)
    assert GeometryEntity.encloses(c, Point(0, 0))
    assert GeometryEntity.encloses(c, Segment((0, 0), (1, 1)))
    assert GeometryEntity.encloses(c, Line((0, 0), (1, 1))) is False
    assert GeometryEntity.encloses(c, Circle((0, 0), 4))
    assert GeometryEntity.encloses(c, Polygon(Point(0, 0), Point(1, 0), Point(0, 1)))
    assert GeometryEntity.encloses(c, RegularPolygon(Point(8, 8), 1, 3)) is False


def test_svg():
    a = Symbol('a')
    b = Symbol('b')
    d = Symbol('d')

    entity = Circle(Point(a, b), d)
    assert entity._repr_svg_() is None

    entity = Circle(Point(0, 0), S.Infinity)
    assert entity._repr_svg_() is None


def test_subs():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)
    p = Point(x, 2)
    q = Point(1, 1)
    r = Point(3, 4)
    for o in [p,
              Segment(p, q),
              Ray(p, q),
              Line(p, q),
              Triangle(p, q, r),
              RegularPolygon(p, 3, 6),
              Polygon(p, q, r, Point(5, 4)),
              Circle(p, 3),
              Ellipse(p, 3, 4)]:
        assert 'y' in str(o.subs(x, y))
    assert p.subs({x: 1}) == Point(1, 2)
    assert Point(1, 2).subs(Point(1, 2), Point(3, 4)) == Point(3, 4)
    assert Point(1, 2).subs((1, 2), Point(3, 4)) == Point(3, 4)
    assert Point(1, 2).subs(Point(1, 2), Point(3, 4)) == Point(3, 4)
    assert Point(1, 2).subs({(1, 2)}) == Point(2, 2)
    raises(ValueError, lambda: Point(1, 2).subs(1))
    raises(ValueError, lambda: Point(1, 1).subs((Point(1, 1), Point(1,
           2)), 1, 2))


def test_transform():
    assert scale(1, 2, (3, 4)).tolist() == \
        [[1, 0, 0], [0, 2, 0], [0, -4, 1]]


def test_reflect_entity_overrides():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)
    b = Symbol('b')
    m = Symbol('m')
    l = Line((0, b), slope=m)
    p = Point(x, y)
    r = p.reflect(l)
    c = Circle((x, y), 3)
    cr = c.reflect(l)
    assert cr == Circle(r, -3)
    assert c.area == -cr.area

    pent = RegularPolygon((1, 2), 1, 5)
    l = Line(pent.vertices[1],
        slope=Rational(random() - .5, random() - .5))
    rpent = pent.reflect(l)
    assert rpent.center == pent.center.reflect(l)
    rvert = [i.reflect(l) for i in pent.vertices]
    for v in rpent.vertices:
        for i in range(len(rvert)):
            ri = rvert[i]
            if ri.equals(v):
                rvert.remove(ri)
                break
    assert not rvert
    assert pent.area.equals(-rpent.area)
