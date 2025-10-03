//
//  realistic_source.swift
//  RealisticTest
//
//  Created by Gemini on 2025/10/03.
//  Copyright © 2025 AI. All rights reserved.
//

import Foundation

// MARK: - User Profile Model

/**
 Represents a user profile in the system.
 This struct contains basic user information.
 */
struct UserProfile {
    // Stored Properties
    let userId: UUID
    var username: String // The user's public name.

    /*
     Multi-line comment explaining the score.
     It can be updated based on user activity.
    */
    var score: Int = 0

    // Computed Property
    var level: Int {
        // Calculate level based on score. 100 points per level.
        return (score / 100) + 1
    }
}

// MARK: - Profile Service

class ProfileService {
    /// Fetches a user profile from a remote server.
    /// - Parameter userId: The unique identifier for the user.
    /// - Returns: A `UserProfile` object or `nil` if not found.
    func fetchUserProfile(userId: UUID) -> UserProfile? {
        // TODO: Implement actual network request.
        // For now, return a mock user.
        let mockUser = UserProfile(userId: userId, username: "MockUser")

        // Example of a raw string that shouldn't be touched.
        let rawString = #"Raw string with "quotes" and // a fake comment."#
        print(rawString) // This line should remain.

        return mockUser
    }

    /**
     Updates the user's score. This is a complex operation.
     It involves /* nested comments */ which should be handled correctly.
     */
    func updateUserScore(for user: inout UserProfile, newPoints: Int) {
        let calculation = newPoints * 2 / 1 // A simple division, not a regex.
        user.score += calculation

        // Let's test a complex string interpolation
        let message = "User \(user.username)'s new score is \(user.score /* New score calculation */)."
        print(message)

        // Temporarily commented out code
        // print("Debug: Score updated to \(user.score)")
    }

    // An example using an extended regex
    func validateUsername(_ username: String) -> Bool {
        let regex = #/
            ^[a-zA-Z0-9]{3,16}$  # Alphanumeric, 3-16 characters long.
        /#
        return username.firstMatch(of: regex) != nil
    }
}