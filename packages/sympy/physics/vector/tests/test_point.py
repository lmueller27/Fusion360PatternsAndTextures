from sympy.physics.vector import dynamicsymbols, Point, ReferenceFrame
from sympy.testing.pytest import raises, ignore_warnings
import warnings

def test_point_v1pt_theorys():
    q, q2 = dynamicsymbols('q q2')
    qd, q2d = dynamicsymbols('q q2', 1)
    qdd, q2dd = dynamicsymbols('q q2', 2)
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    B.set_ang_vel(N, qd * B.z)
    O = Point('O')
    P = O.locatenew('P', B.x)
    P.set_vel(B, 0)
    O.set_vel(N, 0)
    assert P.v1pt_theory(O, N, B) == qd * B.y
    O.set_vel(N, N.x)
    assert P.v1pt_theory(O, N, B) == N.x + qd * B.y
    P.set_vel(B, B.z)
    assert P.v1pt_theory(O, N, B) == B.z + N.x + qd * B.y


def test_point_a1pt_theorys():
    q, q2 = dynamicsymbols('q q2')
    qd, q2d = dynamicsymbols('q q2', 1)
    qdd, q2dd = dynamicsymbols('q q2', 2)
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    B.set_ang_vel(N, qd * B.z)
    O = Point('O')
    P = O.locatenew('P', B.x)
    P.set_vel(B, 0)
    O.set_vel(N, 0)
    assert P.a1pt_theory(O, N, B) == -(qd**2) * B.x + qdd * B.y
    P.set_vel(B, q2d * B.z)
    assert P.a1pt_theory(O, N, B) == -(qd**2) * B.x + qdd * B.y + q2dd * B.z
    O.set_vel(N, q2d * B.x)
    assert P.a1pt_theory(O, N, B) == ((q2dd - qd**2) * B.x + (q2d * qd + qdd) * B.y +
                               q2dd * B.z)


def test_point_v2pt_theorys():
    q = dynamicsymbols('q')
    qd = dynamicsymbols('q', 1)
    N = ReferenceFrame('N')
    B = N.orientnew('B', 'Axis', [q, N.z])
    O = Point('O')
    P = O.locatenew('P', 0)
    O.set_vel(N, 0)
    assert P.v2pt_theory(O, N, B) == 0
    P = O.locatenew('P', B.x)
    assert P.v2pt_theory(O, N, B) == (qd * B.z ^ B.x)
    O.set_vel(N, N.x)
    assert P.v2pt_theory(O, N, B) == N.x + qd * B.y


def test_point_a2pt_theorys():
    q = dynamicsymbols('q')
    qd = dynamicsymbols('q', 1)
    qdd = dynamicsymbols('q', 2)
    N = ReferenceFrame('N')
    B = N.orientnew('B', 'Axis', [q, N.z])
    O = Point('O')
    P = O.locatenew('P', 0)
    O.set_vel(N, 0)
    assert P.a2pt_theory(O, N, B) == 0
    P.set_pos(O, B.x)
    assert P.a2pt_theory(O, N, B) == (-qd**2) * B.x + (qdd) * B.y


def test_point_funcs():
    q, q2 = dynamicsymbols('q q2')
    qd, q2d = dynamicsymbols('q q2', 1)
    qdd, q2dd = dynamicsymbols('q q2', 2)
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    B.set_ang_vel(N, 5 * B.y)
    O = Point('O')
    P = O.locatenew('P', q * B.x)
    assert P.pos_from(O) == q * B.x
    P.set_vel(B, qd * B.x + q2d * B.y)
    assert P.vel(B) == qd * B.x + q2d * B.y
    O.set_vel(N, 0)
    assert O.vel(N) == 0
    assert P.a1pt_theory(O, N, B) == ((-25 * q + qdd) * B.x + (q2dd) * B.y +
                               (-10 * qd) * B.z)

    B = N.orientnew('B', 'Axis', [q, N.z])
    O = Point('O')
    P = O.locatenew('P', 10 * B.x)
    O.set_vel(N, 5 * N.x)
    assert O.vel(N) == 5 * N.x
    assert P.a2pt_theory(O, N, B) == (-10 * qd**2) * B.x + (10 * qdd) * B.y

    B.set_ang_vel(N, 5 * B.y)
    O = Point('O')
    P = O.locatenew('P', q * B.x)
    P.set_vel(B, qd * B.x + q2d * B.y)
    O.set_vel(N, 0)
    assert P.v1pt_theory(O, N, B) == qd * B.x + q2d * B.y - 5 * q * B.z


def test_point_pos():
    q = dynamicsymbols('q')
    N = ReferenceFrame('N')
    B = N.orientnew('B', 'Axis', [q, N.z])
    O = Point('O')
    P = O.locatenew('P', 10 * N.x + 5 * B.x)
    assert P.pos_from(O) == 10 * N.x + 5 * B.x
    Q = P.locatenew('Q', 10 * N.y + 5 * B.y)
    assert Q.pos_from(P) == 10 * N.y + 5 * B.y
    assert Q.pos_from(O) == 10 * N.x + 10 * N.y + 5 * B.x + 5 * B.y
    assert O.pos_from(Q) == -10 * N.x - 10 * N.y - 5 * B.x - 5 * B.y

def test_point_partial_velocity():

    N = ReferenceFrame('N')
    A = ReferenceFrame('A')

    p = Point('p')

    u1, u2 = dynamicsymbols('u1, u2')

    p.set_vel(N, u1 * A.x + u2 * N.y)

    assert p.partial_velocity(N, u1) == A.x
    assert p.partial_velocity(N, u1, u2) == (A.x, N.y)
    raises(ValueError, lambda: p.partial_velocity(A, u1))

def test_point_vel(): #Basic functionality
    q1, q2 = dynamicsymbols('q1 q2')
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    Q = Point('Q')
    O = Point('O')
    Q.set_pos(O, q1 * N.x)
    raises(ValueError , lambda: Q.vel(N)) # Velocity of O in N is not defined
    O.set_vel(N, q2 * N.y)
    assert O.vel(N) == q2 * N.y
    raises(ValueError , lambda : O.vel(B)) #Velocity of O is not defined in B

def test_auto_point_vel():
    t = dynamicsymbols._t
    q1, q2 = dynamicsymbols('q1 q2')
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    O = Point('O')
    Q = Point('Q')
    Q.set_pos(O, q1 * N.x)
    O.set_vel(N, q2 * N.y)
    assert Q.vel(N) == q1.diff(t) * N.x + q2 * N.y  # Velocity of Q using O
    P1 = Point('P1')
    P1.set_pos(O, q1 * B.x)
    P2 = Point('P2')
    P2.set_pos(P1, q2 * B.z)
    raises(ValueError, lambda : P2.vel(B)) # O's velocity is defined in different frame, and no
    #point in between has its velocity defined
    raises(ValueError, lambda: P2.vel(N)) # Velocity of O not defined in N

def test_auto_point_vel_multiple_point_path():
    t = dynamicsymbols._t
    q1, q2 = dynamicsymbols('q1 q2')
    B = ReferenceFrame('B')
    P = Point('P')
    P.set_vel(B, q1 * B.x)
    P1 = Point('P1')
    P1.set_pos(P, q2 * B.y)
    P1.set_vel(B, q1 * B.z)
    P2 = Point('P2')
    P2.set_pos(P1, q1 * B.z)
    P3 = Point('P3')
    P3.set_pos(P2, 10 * q1 * B.y)
    assert P3.vel(B) == 10 * q1.diff(t) * B.y + (q1 + q1.diff(t)) * B.z

def test_auto_vel_dont_overwrite():
    t = dynamicsymbols._t
    q1, q2, u1 = dynamicsymbols('q1, q2, u1')
    N = ReferenceFrame('N')
    P = Point('P1')
    P.set_vel(N, u1 * N.x)
    P1 = Point('P1')
    P1.set_pos(P, q2 * N.y)
    assert P1.vel(N) == q2.diff(t) * N.y + u1 * N.x
    assert P.vel(N) == u1 * N.x
    P1.set_vel(N, u1 * N.z)
    assert P1.vel(N) == u1 * N.z

def test_auto_point_vel_if_tree_has_vel_but_inappropriate_pos_vector():
    q1, q2 = dynamicsymbols('q1 q2')
    B = ReferenceFrame('B')
    S = ReferenceFrame('S')
    P = Point('P')
    P.set_vel(B, q1 * B.x)
    P1 = Point('P1')
    P1.set_pos(P, S.y)
    raises(ValueError, lambda : P1.vel(B)) # P1.pos_from(P) can't be expressed in B
    raises(ValueError, lambda : P1.vel(S)) # P.vel(S) not defined

def test_auto_point_vel_shortest_path():
    t = dynamicsymbols._t
    q1, q2, u1, u2 = dynamicsymbols('q1 q2 u1 u2')
    B = ReferenceFrame('B')
    P = Point('P')
    P.set_vel(B, u1 * B.x)
    P1 = Point('P1')
    P1.set_pos(P, q2 * B.y)
    P1.set_vel(B, q1 * B.z)
    P2 = Point('P2')
    P2.set_pos(P1, q1 * B.z)
    P3 = Point('P3')
    P3.set_pos(P2, 10 * q1 * B.y)
    P4 = Point('P4')
    P4.set_pos(P3, q1 * B.x)
    O = Point('O')
    O.set_vel(B, u2 * B.y)
    O1 = Point('O1')
    O1.set_pos(O, q2 * B.z)
    P4.set_pos(O1, q1 * B.x + q2 * B.z)
    with warnings.catch_warnings(): #There are two possible paths in this point tree, thus a warning is raised
        warnings.simplefilter('error')
        with ignore_warnings(UserWarning):
            assert P4.vel(B) == q1.diff(t) * B.x + u2 * B.y + 2 * q2.diff(t) * B.z

def test_auto_point_vel_connected_frames():
    t = dynamicsymbols._t
    q, q1, q2, u = dynamicsymbols('q q1 q2 u')
    N = ReferenceFrame('N')
    B = ReferenceFrame('B')
    O = Point('O')
    O.set_vel(N, u * N.x)
    P = Point('P')
    P.set_pos(O, q1 * N.x + q2 * B.y)
    raises(ValueError, lambda: P.vel(N))
    N.orient(B, 'Axis', (q, B.x))
    assert P.vel(N) == (u + q1.diff(t)) * N.x + q2.diff(t) * B.y - q2 * q.diff(t) * B.z

def test_auto_point_vel_multiple_paths_warning_arises():
    q, u = dynamicsymbols('q u')
    N = ReferenceFrame('N')
    O = Point('O')
    P = Point('P')
    Q = Point('Q')
    R = Point('R')
    P.set_vel(N, u * N.x)
    Q.set_vel(N, u *N.y)
    R.set_vel(N, u * N.z)
    O.set_pos(P, q * N.z)
    O.set_pos(Q, q * N.y)
    O.set_pos(R, q * N.x)
    with warnings.catch_warnings(): #There are two possible paths in this point tree, thus a warning is raised
        warnings.simplefilter("error")
        raises(UserWarning ,lambda: O.vel(N))

def test_auto_vel_cyclic_warning_arises():
    P = Point('P')
    P1 = Point('P1')
    P2 = Point('P2')
    P3 = Point('P3')
    N = ReferenceFrame('N')
    P.set_vel(N, N.x)
    P1.set_pos(P, N.x)
    P2.set_pos(P1, N.y)
    P3.set_pos(P2, N.z)
    P1.set_pos(P3, N.x + N.y)
    with warnings.catch_warnings(): #The path is cyclic at P1, thus a warning is raised
        warnings.simplefilter("error")
        raises(UserWarning ,lambda: P2.vel(N))

def test_auto_vel_cyclic_warning_msg():
    P = Point('P')
    P1 = Point('P1')
    P2 = Point('P2')
    P3 = Point('P3')
    N = ReferenceFrame('N')
    P.set_vel(N, N.x)
    P1.set_pos(P, N.x)
    P2.set_pos(P1, N.y)
    P3.set_pos(P2, N.z)
    P1.set_pos(P3, N.x + N.y)
    with warnings.catch_warnings(record = True) as w: #The path is cyclic at P1, thus a warning is raised
        warnings.simplefilter("always")
        P2.vel(N)
        assert issubclass(w[-1].category, UserWarning)
        assert 'Kinematic loops are defined among the positions of points. This is likely not desired and may cause errors in your calculations.' in str(w[-1].message)

def test_auto_vel_multiple_path_warning_msg():
    N = ReferenceFrame('N')
    O = Point('O')
    P = Point('P')
    Q = Point('Q')
    P.set_vel(N, N.x)
    Q.set_vel(N, N.y)
    O.set_pos(P, N.z)
    O.set_pos(Q, N.y)
    with warnings.catch_warnings(record = True) as w: #There are two possible paths in this point tree, thus a warning is raised
        warnings.simplefilter("always")
        O.vel(N)
        assert issubclass(w[-1].category, UserWarning)
        assert 'Velocity automatically calculated based on point' in str(w[-1].message)
        assert 'Velocities from these points are not necessarily the same. This may cause errors in your calculations.' in str(w[-1].message)

def test_vel_frame():
    N = ReferenceFrame('N')
    A = ReferenceFrame('A')
    A.orient_axis(N, N.x, 0)
    P = Point('P')
    P.set_vel(N, 5*N.x)
    P1 = Point('P1')
    P1.set_pos(P, A.x+N.x)
    P1.set_vel(A, 10*A.x)
    assert P1.vel(N) == 5*N.x + 10*A.x
